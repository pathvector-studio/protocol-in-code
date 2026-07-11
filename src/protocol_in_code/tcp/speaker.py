from __future__ import annotations

from dataclasses import dataclass, field

from .congestion import CongestionState, on_ack as congestion_on_ack, on_timeout as congestion_on_timeout
from .fast_retransmit import AckSignal, AckTracker, on_ack as track_ack
from .handshake import ConnectionState, HandshakeStep
from .handshake import active_open as handshake_active_open
from .handshake import on_segment as handshake_on_segment
from .reassembly import DeliveryOutcome, ReassemblyBuffer, deliver
from .reset import ResetDisposition, on_reset
from .rto import RttEstimator
from .segment import Segment, flags_label, is_fin, is_rst
from .teardown import CloseState, initiate_close, on_segment_active, on_segment_passive, passive_close
from .window import ReceiveBuffer, advertised_window

MSS = 1

# CloseState.ESTABLISHED and ConnectionState.ESTABLISHED are two enums that mean the same
# thing at two different moments in one connection's life; the endpoint below tracks both
# spaces in a single `state` field by storing whichever enum member currently applies.


@dataclass
class ToyTcpEndpoint:
    """Build the toy TCP loop: one endpoint's state, wired to every session in this track."""

    name: str
    iss: int
    state: object = ConnectionState.CLOSED
    clock: int = 0
    rcv_nxt: int = 0
    recv_buffer: ReceiveBuffer = field(default_factory=lambda: ReceiveBuffer(capacity=4096))
    reassembly: ReassemblyBuffer | None = None
    estimator: RttEstimator = field(default_factory=RttEstimator)
    congestion: CongestionState = field(default_factory=CongestionState)
    ack_tracker: AckTracker = field(default_factory=AckTracker)
    time_wait_entered_at: int | None = None
    trace: list[str] = field(default_factory=list)

    def tick(self, seconds: int) -> None:
        self.clock += seconds
        if self.state is CloseState.TIME_WAIT and self.time_wait_entered_at is not None:
            from .teardown import time_wait_expired

            if time_wait_expired(self.time_wait_entered_at, self.clock):
                self.state = CloseState.CLOSED
                self.trace.append(f"{self.name}: time-wait expired at clock={self.clock}, closed")

    def listen(self) -> None:
        self.state = ConnectionState.LISTEN
        self.trace.append(f"{self.name}: listening")

    def active_open(self) -> Segment:
        """The client's first move: emit a SYN and remember we're waiting for the reply."""
        self.state, syn = handshake_active_open(self.iss)
        self.trace.append(f"{self.name}: active-open, sent {flags_label(syn)} seq={syn.seq}")
        return syn

    def on_segment(self, segment: Segment) -> Segment | None:
        """Dispatch by current state and flags - handshake, reset, teardown, then data."""
        reset_outcome = on_reset(self.state, segment, self.rcv_nxt, advertised_window(self.recv_buffer))
        if reset_outcome.disposition is ResetDisposition.ACCEPTED:
            self.state = CloseState.CLOSED
            self.trace.append(f"{self.name}: {reset_outcome.note}")
            return None

        if isinstance(self.state, ConnectionState) and self.state is not ConnectionState.ESTABLISHED:
            step = handshake_on_segment(self.state, segment, self.iss)
            self.state = step.new_state
            self.trace.append(f"{self.name}: {step.note} -> {step.new_state.value}")
            if step.new_state is ConnectionState.ESTABLISHED:
                self.rcv_nxt = segment.seq + (1 if segment.payload_len == 0 else segment.payload_len)
                self.reassembly = ReassemblyBuffer(rcv_nxt=self.rcv_nxt)
            return step.reply

        if isinstance(self.state, CloseState):
            return self._on_segment_teardown(segment)

        # ESTABLISHED and carrying data or a peer-initiated FIN.
        if is_fin(segment):
            step = on_segment_passive(CloseState.ESTABLISHED, segment)
            self.state = step.new_state
            self.trace.append(f"{self.name}: {step.note} -> {step.new_state.value}")
            return step.reply

        return self._on_data(segment)

    def _on_data(self, segment: Segment) -> None:
        if segment.payload_len <= 0 or self.reassembly is None:
            return None
        result = deliver(self.reassembly, segment.seq, segment.payload_len)
        self.rcv_nxt = result.new_rcv_nxt
        self.trace.append(f"{self.name}: data seq={segment.seq} -> {result.outcome.value}, rcv_nxt={self.rcv_nxt}")
        signal = track_ack(self.ack_tracker, segment.ack)
        if signal is AckSignal.FAST_RETRANSMIT:
            congestion_on_timeout(self.congestion)
            self.trace.append(f"{self.name}: {AckSignal.FAST_RETRANSMIT.value}, cwnd={self.congestion.cwnd}")
        elif signal is AckSignal.NEW_DATA_ACKED:
            congestion_on_ack(self.congestion)
        return None

    def _on_segment_teardown(self, segment: Segment) -> Segment | None:
        if self.state is CloseState.CLOSE_WAIT:
            return None  # only close() drives this state forward, not an incoming segment

        # LAST_ACK belongs to the passive closer's path; every other close state here
        # (FIN_WAIT_1, FIN_WAIT_2, CLOSING) belongs to the active closer's path.
        if self.state is CloseState.LAST_ACK:
            step = on_segment_passive(self.state, segment)
        else:
            step = on_segment_active(self.state, segment, self.clock)

        self.state = step.new_state
        self.trace.append(f"{self.name}: {step.note} -> {step.new_state.value}")
        if step.new_state is CloseState.TIME_WAIT:
            self.time_wait_entered_at = step.wait_started_at
        return step.reply

    def close(self) -> Segment:
        """Either close the connection actively (send FIN first) or answer a pending FIN."""
        if self.state is CloseState.CLOSE_WAIT:
            self.state, fin = passive_close(self.iss)
            self.trace.append(f"{self.name}: application close(), sent {flags_label(fin)}")
            return fin

        self.state, fin = initiate_close(self.iss)
        self.trace.append(f"{self.name}: application close(), sent {flags_label(fin)}")
        return fin


def run_three_way_handshake(client: ToyTcpEndpoint, server: ToyTcpEndpoint) -> None:
    """The smallest integration demo: two endpoints trade three segments and both reach ESTABLISHED."""
    server.listen()

    syn = client.active_open()
    syn_ack = server.on_segment(syn)
    assert syn_ack is not None
    final_ack = client.on_segment(syn_ack)
    assert final_ack is not None
    reply = server.on_segment(final_ack)
    assert reply is None
