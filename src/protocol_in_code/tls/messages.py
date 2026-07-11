from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class HelloValidity(str, Enum):
    VALID = "Valid"
    NO_VERSIONS = "NoVersions"
    NO_CIPHER_SUITES = "NoCipherSuites"
    EMPTY_SERVER_NAME = "EmptyServerName"


@dataclass(frozen=True)
class ClientHello:
    """A hello is a declaration of capabilities, an ordinary object you can print."""

    offered_versions: tuple[str, ...]
    cipher_suites: tuple[str, ...]
    server_name: str
    alpn: tuple[str, ...] = ()
    session_ticket: str | None = None


@dataclass(frozen=True)
class ServerHello:
    """The server's reply is not a new declaration - it is one pick from the client's list."""

    chosen_version: str
    chosen_suite: str
    chosen_alpn: str | None = None


def validate_client_hello(hello: ClientHello) -> HelloValidity:
    """A hello that declares nothing usable is invalid before negotiation even starts."""
    if not hello.offered_versions:
        return HelloValidity.NO_VERSIONS
    if not hello.cipher_suites:
        return HelloValidity.NO_CIPHER_SUITES
    if hello.server_name == "":
        return HelloValidity.EMPTY_SERVER_NAME
    return HelloValidity.VALID
