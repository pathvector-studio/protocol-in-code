from __future__ import annotations

from dataclasses import dataclass

from .checksum import internet_checksum, verify_checksum
from .dispatch import LayerId, next_layer, transport_protocol
from .ethernet import EthernetHeader, EthernetOutcome, parse_ethernet
from .ip import Ipv4Header, Ipv4Outcome, parse_ipv4

# The classic pcap file format: a 24-byte global header, then a stream of
# (16-byte record header, packet bytes) pairs. The global header's magic
# number is stored in the file's OWN byte order, so reading it correctly
# is the first decision every parser has to make -- that's the lesson hook.
MAGIC_BIG_ENDIAN = 0xA1B2C3D4
MAGIC_LITTLE_ENDIAN_ON_WIRE = 0xD4C3B2A1

GLOBAL_HEADER_LEN = 24
RECORD_HEADER_LEN = 16

PCAP_VERSION_MAJOR = 2
PCAP_VERSION_MINOR = 4
LINKTYPE_ETHERNET = 1


@dataclass(frozen=True)
class PcapGlobalHeader:
    magic: int
    version_major: int
    version_minor: int
    snaplen: int
    network: int


@dataclass(frozen=True)
class PacketSummary:
    ethernet: EthernetHeader | None
    ip: Ipv4Header | None
    transport: LayerId
    checksum_ok: bool | None


@dataclass(frozen=True)
class PcapReadResult:
    global_header: PcapGlobalHeader | None
    packets: tuple[PacketSummary, ...]
    trace: tuple[str, ...]


def _detect_byte_order(magic_bytes: bytes) -> str | None:
    """The four magic bytes read one way say 'big-endian file'; the other way, 'little-endian file'."""
    big = int.from_bytes(magic_bytes, "big")
    little = int.from_bytes(magic_bytes, "little")
    if big == MAGIC_BIG_ENDIAN:
        return "big"
    if little == MAGIC_BIG_ENDIAN and big == MAGIC_LITTLE_ENDIAN_ON_WIRE:
        return "little"
    return None


def read_pcap(data: bytes) -> PcapReadResult:
    """Read the global header, then walk records, handing each packet down the stack we already built."""
    trace: list[str] = []

    if len(data) < GLOBAL_HEADER_LEN:
        trace.append("global header: TooShort")
        return PcapReadResult(None, (), tuple(trace))

    order = _detect_byte_order(data[0:4])
    if order is None:
        trace.append("global header: BadMagic")
        return PcapReadResult(None, (), tuple(trace))
    trace.append(f"global header: magic identifies {order}-endian file")

    magic = int.from_bytes(data[0:4], order)
    version_major = int.from_bytes(data[4:6], order)
    version_minor = int.from_bytes(data[6:8], order)
    snaplen = int.from_bytes(data[16:20], order)
    network = int.from_bytes(data[20:24], order)
    global_header = PcapGlobalHeader(magic, version_major, version_minor, snaplen, network)

    packets: list[PacketSummary] = []
    offset = GLOBAL_HEADER_LEN

    while offset < len(data):
        if offset + RECORD_HEADER_LEN > len(data):
            trace.append(f"record at {offset}: TooShortForRecordHeader")
            break

        incl_len = int.from_bytes(data[offset + 8 : offset + 12], order)
        record_start = offset + RECORD_HEADER_LEN
        record_end = record_start + incl_len
        if record_end > len(data):
            trace.append(f"record at {offset}: TooShortForPayload")
            break

        packet_bytes = data[record_start:record_end]
        packets.append(_summarize_packet(packet_bytes, len(packets), trace))

        offset = record_end

    return PcapReadResult(global_header, tuple(packets), tuple(trace))


def _summarize_packet(packet_bytes: bytes, index: int, trace: list[str]) -> PacketSummary:
    """One packet, three layers: Ethernet peels off, dispatch names IPv4, IP peels off, checksum judges it."""
    eth_parse = parse_ethernet(packet_bytes)
    if eth_parse.outcome is not EthernetOutcome.OK:
        trace.append(f"packet {index}: ethernet {eth_parse.outcome.value}")
        return PacketSummary(None, None, LayerId.UNKNOWN, None)

    assert eth_parse.header is not None
    layer = next_layer(eth_parse.header.ethertype)
    trace.append(f"packet {index}: ethernet OK, ethertype -> {layer.value}")

    if layer is not LayerId.IPV4:
        return PacketSummary(eth_parse.header, None, LayerId.UNKNOWN, None)

    ip_parse = parse_ipv4(eth_parse.payload)
    if ip_parse.outcome is not Ipv4Outcome.OK:
        trace.append(f"packet {index}: ip {ip_parse.outcome.value}")
        return PacketSummary(eth_parse.header, None, LayerId.UNKNOWN, None)

    assert ip_parse.header is not None
    transport = transport_protocol(ip_parse.header.protocol)
    trace.append(f"packet {index}: ip OK, protocol -> {transport.value}")

    header_bytes = eth_parse.payload[: ip_parse.header.header_len_bytes]
    checksum_ok = verify_checksum(header_bytes)
    trace.append(f"packet {index}: checksum {'valid' if checksum_ok else 'INVALID'}")

    return PacketSummary(eth_parse.header, ip_parse.header, transport, checksum_ok)


def _global_header_bytes() -> bytes:
    """Little-endian global header: the same 24 fields any libpcap file starts with."""
    return (
        MAGIC_BIG_ENDIAN.to_bytes(4, "little")
        + PCAP_VERSION_MAJOR.to_bytes(2, "little")
        + PCAP_VERSION_MINOR.to_bytes(2, "little")
        + (0).to_bytes(4, "little", signed=True)  # thiszone
        + (0).to_bytes(4, "little")  # sigfigs
        + (65535).to_bytes(4, "little")  # snaplen
        + LINKTYPE_ETHERNET.to_bytes(4, "little")
    )


def _record_bytes(packet_bytes: bytes, ts_sec: int) -> bytes:
    """One 16-byte record header followed by the packet it describes."""
    length = len(packet_bytes)
    return (
        ts_sec.to_bytes(4, "little")
        + (0).to_bytes(4, "little")  # ts_usec
        + length.to_bytes(4, "little")  # incl_len
        + length.to_bytes(4, "little")  # orig_len
        + packet_bytes
    )


def _build_ipv4_header(protocol: int, ttl: int = 64) -> bytes:
    """A minimal 20-byte IPv4 header with a correct checksum, so verify_checksum has something to confirm."""
    version_ihl = (4 << 4) | 5
    header_without_checksum = (
        bytes([version_ihl, 0])  # version/IHL, DSCP/ECN
        + (20).to_bytes(2, "big")  # total length: header only, no payload, for this toy build
        + (0).to_bytes(2, "big")  # identification
        + (0x4000).to_bytes(2, "big")  # flags/fragment offset: DF set
        + bytes([ttl, protocol])
        + (0).to_bytes(2, "big")  # checksum placeholder
        + bytes([10, 0, 0, 1])  # src
        + bytes([10, 0, 0, 2])  # dst
    )
    checksum = internet_checksum(header_without_checksum)
    return header_without_checksum[:10] + checksum.to_bytes(2, "big") + header_without_checksum[12:]


def build_test_pcap() -> bytes:
    """Construct a tiny 2-packet pcap byte-string entirely in code: one valid IPv4/TCP frame, one ARP frame."""
    dst_mac = bytes.fromhex("aabbccddeeff")
    src_mac = bytes.fromhex("112233445566")

    ipv4_frame = dst_mac + src_mac + (0x0800).to_bytes(2, "big") + _build_ipv4_header(protocol=6)
    arp_frame = dst_mac + src_mac + (0x0806).to_bytes(2, "big") + b"\x00" * 28

    body = _record_bytes(ipv4_frame, ts_sec=1) + _record_bytes(arp_frame, ts_sec=2)
    return _global_header_bytes() + body
