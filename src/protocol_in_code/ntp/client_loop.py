"""Build the toy NTP client loop.

A real SNTP client (RFC 5905 section 5, simplified) polls one or more
servers, computes offset and delay for each reply, and only trusts the
sample least likely to be corrupted by network queuing: the one with the
smallest round-trip delay. Delay does not appear in theta's formula (see
offset.py), but a large delay means a long window during which asymmetric
queuing could have crept in on either leg -- so minimum delay is the
client's best proxy for "this sample's symmetry assumption probably held."
Once a sample is chosen, the client nudges its local clock toward the
server's, capped per adjustment so one bad sample cannot cause a large,
suspicious jump (a step); small, capped nudges are a slew.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .offset import Exchange, ExchangeValidity, delay, offset, validate_exchange

MAX_SLEW_PER_ADJUST = 100.0  # milliseconds; a bigger correction gets clamped, not stepped


@dataclass(frozen=True)
class Sample:
    exchange: Exchange
    offset_ms: float
    delay_ms: float


@dataclass
class ToySntpClient:
    local_clock_ms: int = 0
    samples: list[Sample] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)


def sample(client: ToySntpClient, exchange: Exchange) -> Sample | None:
    """Turn one exchange into a Sample, or reject it outright. A malformed
    exchange (see offset.validate_exchange) carries no trustworthy offset or
    delay, so it is logged and dropped rather than fed to the filter.
    """
    validity = validate_exchange(exchange)
    if validity is not ExchangeValidity.VALID:
        client.trace.append(f"rejected: {validity.value}")
        return None

    result = Sample(exchange=exchange, offset_ms=offset(exchange), delay_ms=delay(exchange))
    client.samples.append(result)
    client.trace.append(f"sample: offset={result.offset_ms:+.1f}ms delay={result.delay_ms:.1f}ms")
    return result


def best_sample(client: ToySntpClient) -> Sample | None:
    """The classic NTP filter: minimum delay wins. Low delay is a proxy for
    low queuing on both legs, which is the client's only observable stand-in
    for "the symmetric-path assumption probably held for this one."
    """
    if not client.samples:
        return None
    return min(client.samples, key=lambda s: s.delay_ms)


def apply_correction(client: ToySntpClient, chosen: Sample) -> None:
    """Slew the local clock toward the chosen sample's offset, clamped to
    MAX_SLEW_PER_ADJUST. A single unclamped correction (a step) can leap the
    clock backwards or wildly forwards on one bad sample; a capped slew
    trades speed for safety, moving at most the cap per adjustment.
    """
    correction = max(-MAX_SLEW_PER_ADJUST, min(MAX_SLEW_PER_ADJUST, chosen.offset_ms))
    client.local_clock_ms += round(correction)
    client.trace.append(
        f"apply: offset={chosen.offset_ms:+.1f}ms -> slew={correction:+.1f}ms "
        f"clock={client.local_clock_ms}ms"
    )


def run_sync(client: ToySntpClient, exchanges: tuple[Exchange, ...]) -> Sample | None:
    """Drive one sync round: sample every exchange, pick the min-delay
    survivor, apply its correction, and trace each decision along the way.
    """
    client.trace.append(f"sync start: {len(exchanges)} exchange(s)")

    for exchange in exchanges:
        sample(client, exchange)

    chosen = best_sample(client)
    if chosen is None:
        client.trace.append("sync abandoned: no valid samples")
        return None

    client.trace.append(f"chosen: delay={chosen.delay_ms:.1f}ms (minimum among valid samples)")
    apply_correction(client, chosen)
    return chosen
