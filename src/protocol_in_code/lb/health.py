"""Health is a state machine.

None of the picking strategies (round_robin.py, least_conn.py, hash_pick.py,
ring.py) know whether a backend is actually answering — they only know it
exists. Health tracking is the layer underneath all of them: it turns a
stream of probe results into one of three states, and lb_loop.py filters
every strategy's candidate list through it before picking at all.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

FAIL_THRESHOLD = 3
RISE_THRESHOLD = 2


class BackendHealth(str, Enum):
    HEALTHY = "Healthy"
    SUSPECT = "Suspect"
    DOWN = "Down"


@dataclass
class HealthState:
    status: BackendHealth = BackendHealth.HEALTHY
    consecutive_failures: int = 0
    consecutive_successes: int = 0


def record_probe(state: HealthState, ok: bool) -> BackendHealth:
    """Fold one probe result into the state machine and return the resulting status.

    Going down is fast and coming back is slow, on purpose — this asymmetry
    is called flap damping. A single failed probe demotes HEALTHY to
    SUSPECT immediately (don't keep sending live traffic to a backend that
    just showed a crack), and FAIL_THRESHOLD consecutive failures demotes
    SUSPECT to DOWN. But climbing back up needs RISE_THRESHOLD consecutive
    successes from DOWN, passing back through SUSPECT — one good probe
    right after an outage is not proof the backend is stable, and routing
    real traffic back too eagerly is how a flapping backend takes down
    everything downstream of it.
    """
    if ok:
        state.consecutive_successes += 1
        state.consecutive_failures = 0

        if state.status is BackendHealth.DOWN:
            state.status = BackendHealth.SUSPECT
        elif state.status is BackendHealth.SUSPECT and state.consecutive_successes >= RISE_THRESHOLD:
            state.status = BackendHealth.HEALTHY
    else:
        state.consecutive_failures += 1
        state.consecutive_successes = 0

        if state.status is BackendHealth.HEALTHY:
            state.status = BackendHealth.SUSPECT
        elif state.status is BackendHealth.SUSPECT and state.consecutive_failures >= FAIL_THRESHOLD:
            state.status = BackendHealth.DOWN

    return state.status


def eligible(status: BackendHealth) -> bool:
    """SUSPECT still serves traffic; only DOWN is excluded from routing.

    SUSPECT means "one or more probes failed, but not enough to condemn it"
    — it is a warning label, not a quarantine. Routing still-live traffic to
    a SUSPECT backend is what makes its probes keep running under
    conditions close to real load, and it is what lets it climb back to
    HEALTHY via RISE_THRESHOLD instead of sitting untested in DOWN forever.
    """
    return status is not BackendHealth.DOWN
