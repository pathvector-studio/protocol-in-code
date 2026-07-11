from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class QuestionValidity(str, Enum):
    EMPTY_NAME = "EmptyName"
    NAME_TOO_LONG = "NameTooLong"
    EMPTY_LABEL = "EmptyLabel"
    LABEL_TOO_LONG = "LabelTooLong"
    UNSUPPORTED_TYPE = "UnsupportedType"
    UNSUPPORTED_CLASS = "UnsupportedClass"
    VALID = "Valid"


SUPPORTED_TYPES = ("A", "AAAA", "NS", "CNAME", "MX", "TXT")
SUPPORTED_CLASSES = ("IN",)

MAX_NAME_LENGTH = 253
MAX_LABEL_LENGTH = 63


@dataclass(frozen=True)
class DNSQuestion:
    qname: str
    qtype: str = "A"
    qclass: str = "IN"
    recursion_desired: bool = True


def normalize_name(qname: str) -> str:
    """Lowercase and strip the trailing dot so two spellings of one name compare equal."""
    name = qname.strip().lower()
    if name.endswith("."):
        name = name[:-1]
    return name


def validate_question(question: DNSQuestion) -> QuestionValidity:
    """Decide whether a question is even askable, before any server is contacted."""
    name = normalize_name(question.qname)

    if not name:
        return QuestionValidity.EMPTY_NAME
    if len(name) > MAX_NAME_LENGTH:
        return QuestionValidity.NAME_TOO_LONG

    for label in name.split("."):
        if not label:
            return QuestionValidity.EMPTY_LABEL
        if len(label) > MAX_LABEL_LENGTH:
            return QuestionValidity.LABEL_TOO_LONG

    if question.qtype not in SUPPORTED_TYPES:
        return QuestionValidity.UNSUPPORTED_TYPE
    if question.qclass not in SUPPORTED_CLASSES:
        return QuestionValidity.UNSUPPORTED_CLASS

    return QuestionValidity.VALID


def question_key(question: DNSQuestion) -> tuple[str, str, str]:
    """The identity of a question: two lookups with the same key are the same lookup."""
    return (normalize_name(question.qname), question.qtype, question.qclass)
