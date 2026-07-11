# Session 05 / Module 05: Build the Toy Pcap Reader

## Position

- Track: Packet Parser
- Session: 05
- Site lesson: `pathvector-site/courses/protocols-in-code/parser/module-05/index.html`
- Source file: `src/protocol_in_code/parser/pcap_loop.py`
- Walkthrough script: `examples/parser/session_05_walkthrough.py`

## Core Question

A pcap file is bytes on disk, with no framing beyond "read the next header, then the next record." What does it take to turn that stream into the same layered read — Ethernet, then IPv4, then a checksum verdict — that the last four sessions built one layer at a time?

## Outcome

By the end of this session, the learner should be able to:

- explain why the global header's magic number has to be read two ways before it can be read one way
- trace `read_pcap()`'s loop from the 24-byte global header through each 16-byte record header to the packet bytes it frames
- explain why packet 1 in `build_test_pcap()` has `ip is None` even though `ethernet` parsed cleanly
- name which earlier session's file supplies each piece of `_summarize_packet()`'s layer walk

## Read Order

1. Read the module comment about the classic pcap file format
2. Read `_detect_byte_order()`
3. Read `read_pcap()`'s global header section
4. Read `read_pcap()`'s record loop
5. Read `_summarize_packet()`
6. Read `build_test_pcap()` and its three private builders
7. Run `examples/parser/session_05_walkthrough.py`

## Read It Like Code

```python
PcapGlobalHeader(
    magic,
    version_major,
    version_minor,
    snaplen,
    network,
)

PacketSummary(
    ethernet,
    ip,
    transport,
    checksum_ok,
)

PcapReadResult(
    global_header,
    packets,
    trace,
)
```

## Parts List

Every import at the top of `pcap_loop.py` was taught by an earlier session in this track. The capstone's only new code is the pcap framing around them — the loop that finds where each layer's bytes begin and hands them off.

| Import | Session that taught it | What it contributes to `read_pcap()` |
|---|---|---|
| `checksum.internet_checksum`, `verify_checksum` | 04 | `verify_checksum()` produces `PacketSummary.checksum_ok` from the sliced-out IPv4 header bytes; `internet_checksum()` is used only inside `build_test_pcap()`'s test fixture, not in the read path. |
| `dispatch.LayerId`, `next_layer`, `transport_protocol` | 02 | `next_layer()` turns the Ethernet header's `ethertype` into the branch that decides whether `parse_ipv4()` even runs; `transport_protocol()` turns the IPv4 header's `protocol` field into `PacketSummary.transport`. |
| `ethernet.EthernetHeader`, `EthernetOutcome`, `parse_ethernet` | 01 | `parse_ethernet()` is the first call in `_summarize_packet()`; its `TOO_SHORT` outcome is the first place a packet's walk can stop. |
| `ip.Ipv4Header`, `Ipv4Outcome`, `parse_ipv4` | 03 | `parse_ipv4()` is the second call in `_summarize_packet()`; its header supplies `header_len_bytes`, which slices out exactly the bytes `verify_checksum()` needs. |

`pcap_loop.py` itself adds only the file-framing logic — `_detect_byte_order()`, the global header read, and the record loop — plus `PcapGlobalHeader`, `PacketSummary`, and `PcapReadResult` to hold what the walk finds.

## Decision Flow

```text
read_pcap(data):
  len(data) < 24                      -> trace "TooShort", return (None, (), trace)
  _detect_byte_order(data[0:4]) is None -> trace "BadMagic", return (None, (), trace)
  otherwise -> trace the detected order, read the global header fields in that order

  while offset < len(data):
    remaining bytes < 16               -> trace "TooShortForRecordHeader", stop the loop
    incl_len says the payload runs past len(data) -> trace "TooShortForPayload", stop the loop
    otherwise -> slice out incl_len bytes, hand them to _summarize_packet(), advance offset

_summarize_packet(packet_bytes):
  parse_ethernet() outcome is not OK   -> trace it, return PacketSummary(None, None, UNKNOWN, None)
  next_layer(ethertype) is not IPV4    -> trace ethertype's layer, return PacketSummary(eth, None, UNKNOWN, None)
  parse_ipv4() outcome is not OK       -> trace it, return PacketSummary(eth, None, UNKNOWN, None)
  otherwise -> trace protocol's layer, verify_checksum() on the header slice, return the full PacketSummary
```

## Reading Lens

The important move in this session is to stop reading `_summarize_packet()` as new logic and start reading it as a sequence of calls into files you already know:

- at each `if` in `_summarize_packet()`, which session's outcome enum is being checked, and what does that specific outcome mean back in that session's own module?
- what bytes does each layer hand to the next one — `eth_parse.payload`, then `eth_parse.payload[: ip_parse.header.header_len_bytes]` — and why is that slice exactly right for `verify_checksum()`?
- for a magic-number value that is neither `0xA1B2C3D4` interpreted as big-endian nor as little-endian, what does `_detect_byte_order()` return, and what does `read_pcap()` do with that?

## Toy Model Boundary

This reader handles exactly one pcap variant: the classic (non-pcapng) format, microsecond timestamps only — there is no branch here for the nanosecond-resolution magic number (`0xA1B23C4D`) that real pcap files sometimes use, and no support for the pcapng block-based format at all. Truncated-capture handling stops at what the code actually checks: a record whose header does not fully fit, or whose declared `incl_len` runs past the end of the buffer, ends the read loop and returns whatever packets were already parsed — there is no attempt to recover a partial record or to distinguish "file was truncated mid-write" from "file is simply malformed." The layer walk itself stops at IPv4 plus a checksum verdict; no session in this track has yet taught a TCP or UDP header parser, so `PacketSummary.transport` is a name from `dispatch.py`'s lookup table, not evidence that any transport-layer bytes were actually parsed.

## Code Landmarks

### The module comment

Names the whole file format in three sentences: 24-byte global header, then a stream of 16-byte record headers each followed by the packet it frames, with the magic number stored in the file's own byte order. That last clause is the lesson hook — see the next landmark.

### `_detect_byte_order()`

Reads the same four bytes as both a big-endian integer and a little-endian integer. Whichever interpretation equals `MAGIC_BIG_ENDIAN` (`0xA1B2C3D4`) tells you which order the file was written in — and that answer then governs every other multi-byte field read afterward, not just the magic number itself.

### `read_pcap()`'s two early returns

`TooShort` (fewer than 24 bytes present) and `BadMagic` (24 bytes present, but the magic matches neither byte order) are different failures caught in sequence, and both leave `global_header` as `None`. Neither one raises an exception — the caller reads the outcome from `trace`.

### `_summarize_packet()`'s three descending returns

Each `if` that fails returns immediately with `None` in every field the walk never reached. Reading top to bottom, a `PacketSummary` with `ip=None` tells you precisely which layer stopped the walk, without needing to inspect `trace` at all.

### `build_test_pcap()`'s two packets

Packet 0 is Ethernet + a correctly checksummed IPv4 header with `protocol=6` (TCP) — the full walk succeeds and `checksum_ok` is `True`. Packet 1 is Ethernet + ARP (`ethertype=0x0806`): `next_layer()` returns `LayerId.ARP`, which is not `IPV4`, so `_summarize_packet()` returns with `ip=None` before `parse_ipv4()` is ever called.

## Failure Questions

Use the source file to answer these:

1. `_detect_byte_order()` computes both a big-endian and a little-endian interpretation of the same four bytes before deciding anything. What value would `magic_bytes` have to be for both interpretations to fail, and what does `read_pcap()` do in that case?
2. `read_pcap()` calls `int.from_bytes(data[4:6], order)` for `version_major` using the same `order` that `_detect_byte_order()` returned for the magic number. Why is it safe to reuse that one `order` value for every remaining field in the file, instead of re-detecting it per field?
3. In `_summarize_packet()`, packet 1's `ethernet` field is not `None` but its `ip` field is `None`. Which specific `if` in the function is responsible for that combination, and what condition triggers it?
4. `read_pcap()`'s record loop checks `offset + RECORD_HEADER_LEN > len(data)` before it checks whether the payload fits. Why does the record header length have to be validated before `incl_len` is even read from it?
5. `verify_checksum()` in this module is called on `eth_parse.payload[: ip_parse.header.header_len_bytes]` — not on the whole IPv4 packet. Given what `header_len_bytes` means in `ip.py`, what would go wrong if `verify_checksum()` were instead called on the full payload, including any data after the header?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/parser/session_05_walkthrough.py
```

The walkthrough builds a two-packet pcap in memory with `build_test_pcap()`, reads it with `read_pcap()`, and checks: the global header reports version 2.4 and the Ethernet linktype; exactly two packets come back; packet 0 walks Ethernet through IPv4 to a `TCP` transport label with `checksum_ok` `True`; packet 1 is ARP, stopped after Ethernet with `ip` still `None`; the trace contains the byte-order detection line; a corrupted magic number produces `BadMagic` with no global header and no packets; and two kinds of truncation — cutting the file inside the global header, and cutting it inside the first record header — each produce the exact trace message the source code emits for that case.

## Done When

The learner can say all of the following without looking at notes:

- "The magic number is read two ways on purpose — whichever interpretation matches `0xA1B2C3D4` tells you the file's actual byte order, and that answer decides every later multi-byte read."
- "Every function this file calls to parse a layer was taught in an earlier session; `pcap_loop.py` only adds the file framing around them."
- "A `PacketSummary` with `ip=None` is not an error — it is the record of exactly which layer stopped the walk, readable straight off the returned fields without touching `trace`."

## References

- The libpcap file format (classic, non-pcapng: 24-byte global header, 16-byte per-record headers, microsecond timestamps)
- RFC 791 (Internet Protocol, for the IPv4 header this reader parses)
- RFC 894 (a standard for the transmission of IP datagrams over Ethernet networks, for the Ethernet framing this reader parses)
