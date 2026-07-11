"""Every protocol ends in a loop.

Twenty-two tracks, twenty-two protocols, twenty-two capstone files - and
every single one converges on the same skeleton: hold some state, receive
one event, branch on state crossed with event, mutate the state and emit a
reply (or not), append one line to a trace, and repeat. BGP speaks
UPDATE/WITHDRAW messages, NTP speaks the clock, a pcap parser speaks bytes
off disk - the event source changes every time, but the shape wrapped
around it never does. This file is the course retrospective: a literal
survey of every capstone, one runnable proof that two of the most
different ones share a skeleton, and the punchline stated outright - the
course taught 22 protocols, and it also taught one program, twenty-two
times.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..dns.query import DNSQuestion
from ..dns.resolver import ToyResolver
from ..dns.walk import Zone
from ..tcp.speaker import ToyTcpEndpoint, run_three_way_handshake


@dataclass(frozen=True)
class LoopSummary:
    track: str
    loop_object: str
    event_source: str
    decision_trace: bool


def survey() -> tuple[LoopSummary, ...]:
    """One row per capstone file, listed by hand so the count is honest, not introspected."""
    return (
        LoopSummary("bgp", "bgp/speaker.py:ToySpeaker", "peer UPDATE/WITHDRAW/peer-down messages", True),
        LoopSummary("ospf", "ospf/speaker.py:ToySpeaker", "Hello and LSA flooding messages", True),
        LoopSummary("dns", "dns/resolver.py:ToyResolver", "resolve() calls walking the zone tree", True),
        LoopSummary("tcp", "tcp/speaker.py:ToyTcpEndpoint", "inbound segments plus a clock tick", True),
        LoopSummary("tls", "tls/handshake_loop.py:ToyTlsEndpoint", "handshake messages (ClientHello..Finished)", True),
        LoopSummary("http", "http/server_loop.py:ToyHttpServer", "parsed requests on a connection", True),
        LoopSummary("parser", "parser/pcap_loop.py", "bytes read off a pcap file", True),
        LoopSummary("rpki", "rpki/validator_loop.py:ToyValidator", "announced routes checked against a ROA set", True),
        LoopSummary("dhcp", "dhcp/server_loop.py:ToyDhcpServer", "DISCOVER/REQUEST messages", True),
        LoopSummary("rip", "rip/speaker.py:ToyRipSpeaker", "neighbor advertisements each round", True),
        LoopSummary("nat", "nat/nat_loop.py:ToyNatBox", "inbound/outbound packets plus a clock tick", True),
        LoopSummary("arp", "arp/responder_loop.py:ToyArpNode", "who-has/is-at requests plus queued sends", True),
        LoopSummary("qos", "qos/shaper_loop.py", "packets arriving to be classified and shaped", True),
        LoopSummary("lb", "lb/lb_loop.py:ToyLoadBalancer", "client requests plus health probe results", True),
        LoopSummary("ntp", "ntp/client_loop.py", "server reply exchanges plus the local clock", True),
        LoopSummary("ha", "ha/failover_loop.py", "BFD packets, VRRP advertisements, and a clock tick", True),
        LoopSummary("icmp", "icmp/trace_loop.py:ToyTracer", "TTL-expired/unreachable replies per hop", True),
        LoopSummary("dnssec", "dnssec/validator_loop.py", "RRset + RRSIG lookups walked up the zone chain", True),
        LoopSummary("tcp2", "tcp2/janitor_loop.py", "a clock tick plus scripted housekeeping events", True),
        LoopSummary("ice", "ice/ice_loop.py:ToyIceAgent", "STUN binding responses per candidate pair", True),
        LoopSummary("igmp", "igmp/querier_loop.py:ToyQuerier", "membership reports plus the query cycle clock", True),
        LoopSummary("stp", "stp/stp_loop.py:ToyStpBridge", "BPDUs received each round", True),
    )


def common_skeleton() -> tuple[str, ...]:
    return (
        "hold state",
        "receive one event",
        "branch on state x event",
        "mutate + emit",
        "append one trace line",
        "repeat",
    )


def run_two_loops_side_by_side() -> tuple[str, str]:
    """Run one tiny exchange on two of the most different capstones and pull one trace line from each.

    DNS's ToyResolver is driven by resolve() calls against a zone tree; TCP's
    ToyTcpEndpoint is driven by segments crossing the wire during a three-way
    handshake. Different event sources, same skeleton: both hold state, both
    branch on what just arrived, and both leave behind a trace line recording
    the decision they made.
    """
    zones = {
        "": Zone(name="", delegations=("com",)),
        "com": Zone(name="com", answers={("example.com", "A"): ("93.184.216.34",)}),
    }
    resolver = ToyResolver(zones=zones)
    result = resolver.resolve(DNSQuestion(qname="example.com", qtype="A"))
    dns_line = result.trace[-1]

    client = ToyTcpEndpoint(name="client", iss=1000)
    server = ToyTcpEndpoint(name="server", iss=5000)
    run_three_way_handshake(client, server)
    tcp_line = server.trace[-1]

    return (dns_line, tcp_line)
