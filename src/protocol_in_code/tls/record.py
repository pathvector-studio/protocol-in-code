from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum

# Toy stand-in only: real TLS protects records with an AEAD cipher (e.g. AES-GCM) that
# both encrypts and authenticates in one step. Here the "ciphertext" is the plaintext
# left readable, and the integrity tag is a sha256 hash over (key, seq, plaintext).
# That keeps the envelope metaphor honest without pretending to be real cryptography.


class UnprotectOutcome(str, Enum):
    OK = "Ok"
    BAD_TAG = "BadTag"
    WRONG_KEY = "WrongKey"


@dataclass(frozen=True)
class Record:
    """The record layer is an envelope: content_type and seq ride on the outside, the tag seals the inside."""

    content_type: str
    seq: int
    ciphertext: str
    tag: str


@dataclass(frozen=True)
class UnprotectResult:
    outcome: UnprotectOutcome
    plaintext: str | None


def _tag_for(key: str, seq: int, plaintext: str) -> str:
    material = f"{key}|{seq}|{plaintext}".encode()
    return hashlib.sha256(material).hexdigest()


def protect(plaintext: str, key: str, seq: int, content_type: str = "application_data") -> Record:
    """Sealing a record binds its sequence number into the tag, so replay or reorder breaks it too."""
    tag = _tag_for(key, seq, plaintext)
    return Record(content_type=content_type, seq=seq, ciphertext=plaintext, tag=tag)


def unprotect(record: Record, key: str) -> UnprotectResult:
    """Opening a record recomputes the tag - any mismatch, whether from tampering or the wrong key, fails the same way."""
    expected = _tag_for(key, record.seq, record.ciphertext)
    if record.tag != expected:
        return UnprotectResult(UnprotectOutcome.BAD_TAG, None)
    return UnprotectResult(UnprotectOutcome.OK, record.ciphertext)
