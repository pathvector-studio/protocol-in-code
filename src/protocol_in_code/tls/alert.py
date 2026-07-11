from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .chain import ChainVerdict
from .hostname import HostnameVerdict
from .negotiate import NegotiationOutcome
from .record import UnprotectOutcome


class AlertLevel(str, Enum):
    WARNING = "Warning"
    FATAL = "Fatal"


class AlertDescription(str, Enum):
    CLOSE_NOTIFY = "CloseNotify"
    HANDSHAKE_FAILURE = "HandshakeFailure"
    BAD_RECORD_MAC = "BadRecordMac"
    CERTIFICATE_EXPIRED = "CertificateExpired"
    CERTIFICATE_UNKNOWN = "CertificateUnknown"
    UNKNOWN_CA = "UnknownCa"
    UNRECOGNIZED_NAME = "UnrecognizedName"


class AlertAction(str, Enum):
    IGNORE_AND_CONTINUE = "IgnoreAndContinue"
    CLOSE_CONNECTION = "CloseConnection"


@dataclass(frozen=True)
class Alert:
    """Failure is a typed message: a level plus a description, nothing free-form about it."""

    level: AlertLevel
    description: AlertDescription


def classify(alert: Alert) -> AlertAction:
    """CLOSE_NOTIFY is the orderly goodbye; every other FATAL alert closes just the same."""
    if alert.level is AlertLevel.FATAL:
        return AlertAction.CLOSE_CONNECTION
    if alert.description is AlertDescription.CLOSE_NOTIFY:
        return AlertAction.CLOSE_CONNECTION
    return AlertAction.IGNORE_AND_CONTINUE


def alert_for_negotiation_outcome(outcome: NegotiationOutcome) -> Alert | None:
    """No overlap of any kind is fatal - there is nothing left to negotiate."""
    if outcome is NegotiationOutcome.CHOSEN:
        return None
    return Alert(AlertLevel.FATAL, AlertDescription.HANDSHAKE_FAILURE)


def alert_for_chain_verdict(verdict: ChainVerdict) -> Alert | None:
    """Every non-trusted chain verdict maps to exactly one alert - this table is the reading target."""
    mapping = {
        ChainVerdict.TRUSTED: None,
        ChainVerdict.EMPTY_CHAIN: Alert(AlertLevel.FATAL, AlertDescription.CERTIFICATE_UNKNOWN),
        ChainVerdict.BROKEN_CHAIN: Alert(AlertLevel.FATAL, AlertDescription.CERTIFICATE_UNKNOWN),
        ChainVerdict.EXPIRED: Alert(AlertLevel.FATAL, AlertDescription.CERTIFICATE_EXPIRED),
        ChainVerdict.NOT_YET_VALID: Alert(AlertLevel.FATAL, AlertDescription.CERTIFICATE_EXPIRED),
        ChainVerdict.UNTRUSTED_ROOT: Alert(AlertLevel.FATAL, AlertDescription.UNKNOWN_CA),
    }
    return mapping[verdict]


def alert_for_hostname_verdict(verdict: HostnameVerdict) -> Alert | None:
    """A name mismatch is fatal too - a valid chain for the wrong name is still the wrong server."""
    if verdict is HostnameVerdict.NO_MATCH:
        return Alert(AlertLevel.FATAL, AlertDescription.UNRECOGNIZED_NAME)
    return None


def alert_for_unprotect_outcome(outcome: UnprotectOutcome) -> Alert | None:
    """A record that fails its tag check, for any reason, is reported the same way: bad_record_mac."""
    if outcome is UnprotectOutcome.OK:
        return None
    return Alert(AlertLevel.FATAL, AlertDescription.BAD_RECORD_MAC)
