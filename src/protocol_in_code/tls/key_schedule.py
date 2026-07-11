from __future__ import annotations

import hashlib
from dataclasses import dataclass

# Toy stand-in only: real TLS 1.3 derives keys with HKDF-Extract / HKDF-Expand-Label
# (RFC 8446 SS7.1). Here a single sha256 hexdigest over (secret, label, context) plays
# the role of both extract and expand. No cryptographic strength claim is made.


def derive(secret: str, label: str, context: str = "") -> str:
    """Keys grow on a schedule: every new secret is a hash of the one before it plus a label."""
    material = f"{secret}|{label}|{context}".encode()
    return hashlib.sha256(material).hexdigest()


@dataclass
class KeySchedule:
    """Walk the chain: early_secret -> handshake_secret -> master_secret, each stage derived from the last."""

    early_secret: str
    handshake_secret: str | None = None
    master_secret: str | None = None
    client_hs_traffic: str | None = None
    server_hs_traffic: str | None = None


def start_schedule(psk: str = "") -> KeySchedule:
    """Every schedule begins from a (possibly empty) pre-shared secret, hashed once to seed it."""
    return KeySchedule(early_secret=derive(psk, "early secret"))


def advance_to_handshake(schedule: KeySchedule, shared_key: str) -> None:
    """The (EC)DHE shared key is mixed into the early secret to produce the handshake secret."""
    schedule.handshake_secret = derive(schedule.early_secret, "handshake secret", shared_key)
    schedule.client_hs_traffic = derive(schedule.handshake_secret, "client hs traffic")
    schedule.server_hs_traffic = derive(schedule.handshake_secret, "server hs traffic")


def advance_to_master(schedule: KeySchedule) -> None:
    """The final stage derives from the handshake secret alone - no new external input is mixed in."""
    if schedule.handshake_secret is None:
        raise ValueError("cannot derive master secret before the handshake secret exists")
    schedule.master_secret = derive(schedule.handshake_secret, "master secret")
