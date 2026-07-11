from protocol_in_code.lb.health import BackendHealth, HealthState, eligible, record_probe


def main() -> None:
    print("Session 05 walkthrough: Health is a state machine")
    print()

    state = HealthState()
    marker = "OK" if state.status is BackendHealth.HEALTHY else "NG"
    print(f"[{marker}] fresh state starts HEALTHY    -> {state.status.value}")

    status = record_probe(state, ok=False)
    marker = "OK" if status is BackendHealth.SUSPECT else "NG"
    print(f"[{marker}] 1st failure -> SUSPECT already -> {status.value}")

    status = record_probe(state, ok=False)
    marker = "OK" if status is BackendHealth.SUSPECT else "NG"
    print(f"[{marker}] 2nd failure -> still SUSPECT   -> {status.value} ({state.consecutive_failures} in a row)")

    status = record_probe(state, ok=False)
    marker = "OK" if status is BackendHealth.DOWN else "NG"
    print(f"[{marker}] 3rd failure -> DOWN            -> {status.value} ({state.consecutive_failures} in a row)")

    status = record_probe(state, ok=True)
    marker = "OK" if status is BackendHealth.SUSPECT else "NG"
    print(f"[{marker}] 1st success from DOWN -> SUSPECT -> {status.value}")

    marker = "OK" if status is not BackendHealth.HEALTHY else "NG"
    print(f"[{marker}] 1st success alone is NOT enough -> {status.value} != Healthy")

    status = record_probe(state, ok=True)
    marker = "OK" if status is BackendHealth.HEALTHY else "NG"
    print(f"[{marker}] 2nd consecutive success -> HEALTHY -> {status.value} ({state.consecutive_successes} in a row)")

    marker = "OK" if eligible(BackendHealth.HEALTHY) else "NG"
    print(f"[{marker}] eligible(HEALTHY)              -> {eligible(BackendHealth.HEALTHY)}")

    marker = "OK" if eligible(BackendHealth.SUSPECT) else "NG"
    print(f"[{marker}] eligible(SUSPECT)              -> {eligible(BackendHealth.SUSPECT)} (still serves)")

    marker = "OK" if not eligible(BackendHealth.DOWN) else "NG"
    print(f"[{marker}] eligible(DOWN)                 -> {eligible(BackendHealth.DOWN)} (excluded)")


if __name__ == "__main__":
    main()
