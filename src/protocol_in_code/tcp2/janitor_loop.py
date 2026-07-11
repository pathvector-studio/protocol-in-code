from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ..tcp.teardown import time_wait_expired
from .backlog import AckOutcome, ListenBacklog, SynOutcome, app_accept, on_final_ack, on_syn
from .keepalive import KEEPALIVE_COUNT, KeepaliveVerdict, connection_verdict

# Seconds, same clock the backlog and keepalive files already share (TWO_MSL is 240
# "ticks" in the toy course's own units - see tcp/teardown.py - and keepalive.py's
# constants are seconds; this file treats one clock unit as one second throughout,
# so TWO_MSL reads as 240 seconds here, matching how the rest of tcp2 uses it).


class EventKind(str, Enum):
    """The scripted mix run_day_in_the_life feeds in: one variant per housekeeping story."""

    CONNECT_AND_CLOSE = "ConnectAndClose"       # a short-lived connection: opens, then TIME_WAITs
    IDLE_SILENCE = "IdleSilence"                 # a connection that just... stops talking
    SYN_FLOOD_BURST = "SynFloodBurst"            # many SYNs arrive at once, no real host behind them


@dataclass(frozen=True)
class Event:
    kind: EventKind
    client_tuple: tuple
    count: int = 1  # how many SYNs, for SYN_FLOOD_BURST


@dataclass
class ToyConnectionJanitor:
    """Build the toy connection janitor: none of this is the protocol, it's the housekeeping the protocol leaves behind.

    Three books get kept, and each is kept for a different reason:
      - time_wait_entries: connections that closed cleanly and are now just paying
        the TWO_MSL price from time_wait_cost.py before their port is usable again.
      - idle_connections: connections nobody closed and nobody is actively using -
        keepalive.py's probe schedule is the only thing that will ever notice they
        died.
      - backlog: connections still being born, half-open or waiting on accept() -
        backlog.py's two independent queues.
    """

    backlog: ListenBacklog
    clock: int = 0
    time_wait_entries: dict[tuple, int] = field(default_factory=dict)
    idle_connections: dict[tuple, int] = field(default_factory=dict)
    probe_replies: dict[tuple, tuple[bool, ...]] = field(default_factory=dict)
    cookie_mode: bool = False
    trace: list[str] = field(default_factory=list)

    def enter_time_wait(self, client_tuple: tuple) -> None:
        """A connection closed actively: it stops being 'established' and starts being a held port."""
        self.time_wait_entries[client_tuple] = self.clock
        self.idle_connections.pop(client_tuple, None)
        self.trace.append(f"clock={self.clock}: {client_tuple} entered TIME_WAIT")

    def mark_active(self, client_tuple: tuple) -> None:
        """A connection did something: reset its idle clock, same as touch() in nat/timeout.py."""
        self.idle_connections[client_tuple] = self.clock
        self.probe_replies.pop(client_tuple, None)

    def tick(self, seconds: int) -> None:
        """One housekeeping pass: expire TIME_WAIT, chase idle connections, report backlog pressure."""
        self.clock += seconds
        self._expire_time_wait()
        self._chase_idle_connections()
        self._report_backlog_pressure()

    def _expire_time_wait(self) -> None:
        expired = [
            client_tuple
            for client_tuple, entered_at in self.time_wait_entries.items()
            if time_wait_expired(entered_at, self.clock)
        ]
        for client_tuple in expired:
            del self.time_wait_entries[client_tuple]
        if expired:
            self.trace.append(
                f"clock={self.clock}: TIME_WAIT expired for {len(expired)} connection(s), "
                f"freed ports {expired}"
            )

    def _chase_idle_connections(self) -> None:
        for client_tuple, last_activity in list(self.idle_connections.items()):
            replies = self.probe_replies.get(client_tuple, ())
            verdict = connection_verdict(last_activity, replies, self.clock)

            if verdict is KeepaliveVerdict.PROBING and len(replies) < KEEPALIVE_COUNT:
                # No reply arrived for the newest probe; the real device would resend on
                # its own timer, this toy just records that the probe went unanswered.
                self.probe_replies[client_tuple] = replies + (False,)
                self.trace.append(f"clock={self.clock}: keepalive probe #{len(replies) + 1} to {client_tuple}, no reply")

            if verdict is KeepaliveVerdict.DEAD:
                del self.idle_connections[client_tuple]
                self.probe_replies.pop(client_tuple, None)
                self.trace.append(f"clock={self.clock}: {client_tuple} declared DEAD, keepalive exhausted")

    def _report_backlog_pressure(self) -> None:
        if len(self.backlog.syn_queue) >= self.backlog.syn_limit and not self.cookie_mode:
            self.cookie_mode = True
            self.trace.append(
                f"clock={self.clock}: syn_queue at limit ({self.backlog.syn_limit}), "
                "switching to cookie-mode (see syn_cookies.py) instead of dropping"
            )
        elif len(self.backlog.syn_queue) < self.backlog.syn_limit and self.cookie_mode:
            self.cookie_mode = False
            self.trace.append(f"clock={self.clock}: syn_queue pressure eased, leaving cookie-mode")

    def handle_syn(self, client_tuple: tuple) -> SynOutcome | str:
        """A SYN arrives: normal queueing, unless the janitor already tripped into cookie-mode."""
        if self.cookie_mode:
            self.trace.append(f"clock={self.clock}: SYN from {client_tuple} answered statelessly (cookie-mode)")
            return "cookie-mode"

        outcome = on_syn(self.backlog, client_tuple, self.clock)
        self.trace.append(f"clock={self.clock}: SYN from {client_tuple} -> {outcome.value}")
        self._report_backlog_pressure()
        return outcome

    def handle_final_ack(self, client_tuple: tuple) -> AckOutcome:
        outcome = on_final_ack(self.backlog, client_tuple)
        self.trace.append(f"clock={self.clock}: final ACK from {client_tuple} -> {outcome.value}")
        if outcome is AckOutcome.MOVED_TO_ACCEPT_QUEUE:
            self.mark_active(client_tuple)
        return outcome

    def accept_one(self) -> tuple | None:
        client_tuple = app_accept(self.backlog)
        if client_tuple is not None:
            self.trace.append(f"clock={self.clock}: application accept()ed {client_tuple}")
        return client_tuple


def run_day_in_the_life(janitor: ToyConnectionJanitor, events: tuple[Event, ...]) -> tuple[str, ...]:
    """Feed one scripted day through the janitor: connection churn, an idle death, and a SYN flood.

    This is the capstone's whole point: nothing below is protocol logic. It is a
    dispatcher over the three housekeeping stories tcp2 tells - TIME_WAIT pileup from
    a burst of short connections, an idle connection nobody closed dying only because
    keepalive eventually says so, and a SYN flood that pushes the backlog into
    cookie-mode. The trace on the janitor is the record of every decision along the way.
    """
    for event in events:
        if event.kind is EventKind.CONNECT_AND_CLOSE:
            janitor.handle_syn(event.client_tuple)
            janitor.handle_final_ack(event.client_tuple)
            janitor.accept_one()
            janitor.enter_time_wait(event.client_tuple)

        elif event.kind is EventKind.IDLE_SILENCE:
            janitor.handle_syn(event.client_tuple)
            janitor.handle_final_ack(event.client_tuple)
            janitor.accept_one()
            # mark_active already ran inside handle_final_ack; from here the
            # connection simply goes quiet and the janitor's own ticks do the rest.

        elif event.kind is EventKind.SYN_FLOOD_BURST:
            for i in range(event.count):
                flood_tuple = (*event.client_tuple, i)
                janitor.handle_syn(flood_tuple)
                # No final ACK ever arrives - there is no real host behind these SYNs.

    return tuple(janitor.trace)
