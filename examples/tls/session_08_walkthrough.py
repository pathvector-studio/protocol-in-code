from protocol_in_code.tls.alert import (
    Alert,
    AlertAction,
    AlertDescription,
    AlertLevel,
    alert_for_chain_verdict,
    alert_for_hostname_verdict,
    alert_for_unprotect_outcome,
    classify,
)
from protocol_in_code.tls.chain import ChainVerdict
from protocol_in_code.tls.hostname import HostnameVerdict
from protocol_in_code.tls.record import UnprotectOutcome


def main() -> None:
    print("Session 08 walkthrough: Failure is a typed message")
    print()

    close_notify = Alert(AlertLevel.WARNING, AlertDescription.CLOSE_NOTIFY)
    action = classify(close_notify)
    marker = "OK" if action is AlertAction.CLOSE_CONNECTION else "NG"
    print(f"[{marker}] WARNING close_notify -> CLOSE_CONNECTION -> {action.value}")

    fatal_alert = Alert(AlertLevel.FATAL, AlertDescription.HANDSHAKE_FAILURE)
    action = classify(fatal_alert)
    marker = "OK" if action is AlertAction.CLOSE_CONNECTION else "NG"
    print(f"[{marker}] any FATAL alert -> CLOSE_CONNECTION      -> {action.value}")

    ordinary_warning = Alert(AlertLevel.WARNING, AlertDescription.UNRECOGNIZED_NAME)
    action = classify(ordinary_warning)
    marker = "OK" if action is AlertAction.IGNORE_AND_CONTINUE else "NG"
    print(f"[{marker}] non-close_notify WARNING -> IGNORE        -> {action.value}")

    expired_alert = alert_for_chain_verdict(ChainVerdict.EXPIRED)
    marker = "OK" if expired_alert == Alert(AlertLevel.FATAL, AlertDescription.CERTIFICATE_EXPIRED) else "NG"
    print(f"[{marker}] chain EXPIRED -> CERTIFICATE_EXPIRED       -> {expired_alert}")

    untrusted_root_alert = alert_for_chain_verdict(ChainVerdict.UNTRUSTED_ROOT)
    marker = "OK" if untrusted_root_alert == Alert(AlertLevel.FATAL, AlertDescription.UNKNOWN_CA) else "NG"
    print(f"[{marker}] chain UNTRUSTED_ROOT -> UNKNOWN_CA         -> {untrusted_root_alert}")

    trusted_alert = alert_for_chain_verdict(ChainVerdict.TRUSTED)
    marker = "OK" if trusted_alert is None else "NG"
    print(f"[{marker}] chain TRUSTED -> None (no alert)           -> {trusted_alert}")

    no_match_alert = alert_for_hostname_verdict(HostnameVerdict.NO_MATCH)
    marker = "OK" if no_match_alert == Alert(AlertLevel.FATAL, AlertDescription.UNRECOGNIZED_NAME) else "NG"
    print(f"[{marker}] hostname NO_MATCH -> UNRECOGNIZED_NAME     -> {no_match_alert}")

    bad_tag_alert = alert_for_unprotect_outcome(UnprotectOutcome.BAD_TAG)
    marker = "OK" if bad_tag_alert == Alert(AlertLevel.FATAL, AlertDescription.BAD_RECORD_MAC) else "NG"
    print(f"[{marker}] unprotect BAD_TAG -> BAD_RECORD_MAC        -> {bad_tag_alert}")

    ok_alert = alert_for_unprotect_outcome(UnprotectOutcome.OK)
    marker = "OK" if ok_alert is None else "NG"
    print(f"[{marker}] unprotect OK -> None (no alert)            -> {ok_alert}")


if __name__ == "__main__":
    main()
