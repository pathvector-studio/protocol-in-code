from protocol_in_code.rip.infinity import INFINITY
from protocol_in_code.rip.speaker import ToyRipSpeaker, converge


def main() -> None:
    print("Session 06 walkthrough: Build the toy RIP loop")
    print()

    # A 3-speaker chain: X -- Y -- Z. Only X has a directly connected prefix;
    # Y and Z must learn it hop by hop, the same shape as the smoke test.
    x = ToyRipSpeaker(name="X", connected={"10.0.0.0/24": 1}, neighbors=["Y"])
    y = ToyRipSpeaker(name="Y", neighbors=["X", "Z"])
    z = ToyRipSpeaker(name="Z", neighbors=["Y"])
    speakers = {"X": x, "Y": y, "Z": z}

    report = converge(speakers, rounds=20)

    marker = "OK" if report.converged else "NG"
    print(f"[{marker}] chain converges                 -> converged={report.converged}")

    marker = "OK" if report.rounds_run == 3 else "NG"
    print(f"[{marker}] converges in 3 rounds            -> rounds_run={report.rounds_run}")

    metrics = report.final_tables
    marker = "OK" if (
        metrics["X"]["10.0.0.0/24"] == 1
        and metrics["Y"]["10.0.0.0/24"] == 2
        and metrics["Z"]["10.0.0.0/24"] == 3
    ) else "NG"
    print(f"[{marker}] final metrics form 1/2/3 pattern -> X={metrics['X']} Y={metrics['Y']} Z={metrics['Z']}")

    marker = "OK" if any("Adopted new route" in line for line in y.trace) else "NG"
    print(f"[{marker}] Y's trace shows an adoption      -> {[line for line in y.trace if 'Adopted' in line]}")

    marker = "OK" if len(x.trace) == 0 and len(y.trace) > 0 and len(z.trace) > 0 else "NG"
    print(f"[{marker}] traces non-empty where expected  -> len(x)={len(x.trace)} len(y)={len(y.trace)} len(z)={len(z.trace)}")

    # Now X loses its only connected prefix. lose_connected() poisons it
    # in place rather than deleting it, and one more converge() round
    # should carry that poison all the way down the chain.
    x.lose_connected("10.0.0.0/24")

    marker = "OK" if x.table.routes["10.0.0.0/24"].metric == INFINITY else "NG"
    print(f"[{marker}] X's lost route is poisoned, not deleted -> metric={x.table.routes['10.0.0.0/24'].metric}")

    report2 = converge(speakers, rounds=20)

    marker = "OK" if report2.converged else "NG"
    print(f"[{marker}] chain reconverges after the loss -> converged={report2.converged}")

    metrics2 = report2.final_tables
    marker = "OK" if (
        metrics2["X"]["10.0.0.0/24"] == INFINITY
        and metrics2["Y"]["10.0.0.0/24"] == INFINITY
        and metrics2["Z"]["10.0.0.0/24"] == INFINITY
    ) else "NG"
    print(f"[{marker}] poison propagates to every speaker -> X={metrics2['X']} Y={metrics2['Y']} Z={metrics2['Z']}")

    marker = "OK" if any("lost connected" in line and "poisoned" in line for line in x.trace) else "NG"
    print(f"[{marker}] X's trace records the loss        -> {[line for line in x.trace if 'lost connected' in line]}")


if __name__ == "__main__":
    main()
