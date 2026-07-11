# Session 01 / Module 01: A Query Is a Question Object

## Position

- Track: DNS
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/dns/module-01/index.html`
- Source file: `src/protocol_in_code/dns/query.py`
- Walkthrough script: `examples/dns/session_01_walkthrough.py`

## Core Question

What is a DNS query made of, and when are two lookups actually the same lookup?

## Outcome

By the end of this session, the learner should be able to:

- name the three fields that identify a question: `qname`, `qtype`, `qclass`
- explain why `www.Example.COM.` and `www.example.com` must produce the same key
- list the structural checks a resolver runs before contacting any server
- explain why validation is a separate step from resolution

## Read Order

1. Read `DNSQuestion`
2. Read `normalize_name()`
3. Read `validate_question()`
4. Read `question_key()`
5. Run `examples/dns/session_01_walkthrough.py`
6. Explain each early return in your own words

## Read It Like Code

```python
DNSQuestion(
    qname,
    qtype,
    qclass,
    recursion_desired,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `qname` | The name being asked about. Everything else qualifies this. |
| `qtype` | The same name has different answers for A, AAAA, MX. Type is part of the question. |
| `qclass` | Almost always `IN`, but it is still part of the question's identity. |
| `recursion_desired` | Asks the server to do the walking. It changes who works, not what is asked. |

## Decision Flow

```text
qname empty        -> EmptyName
name > 253 chars   -> NameTooLong
label empty        -> EmptyLabel
label > 63 chars   -> LabelTooLong
qtype unknown      -> UnsupportedType
qclass unknown     -> UnsupportedClass
otherwise          -> Valid
```

## Reading Lens

The important move in this session is to stop thinking of a DNS lookup as "a string goes in, an IP comes out" and start asking:

- what is the full identity of this question?
- which field would make two lookups different?
- which check failed before any packet was sent?

## Toy Model Boundary

Real resolvers parse wire-format messages with compression pointers and EDNS options. This lesson keeps the question as a plain dataclass because the reading target is the identity and validity logic, not the encoding.

`SUPPORTED_TYPES` is deliberately short. Real resolvers know many more types; the branch structure is the same.

## Code Landmarks

### `DNSQuestion`

The dataclass tells you what a question is. Note that the name alone is not the question.

### `normalize_name()`

Case and the trailing dot are spelling, not identity. Normalization runs before every comparison.

### `validate_question()`

The main reading target. Each early return is one structural rule from the protocol, checked before the network is touched.

### `question_key()`

One tuple, three fields. This key is what the cache in Session 04 will use.

## Failure Questions

Use the source file to answer these:

1. What validity comes back for an empty `qname`?
2. What validity comes back for `www..example.com`, and which check catches it?
3. Why does a 64-character label fail while a 63-character label passes?
4. Why does `qtype="LOC"` fail here even though LOC is a real DNS type?
5. Why do `WWW.Example.COM.` and `www.example.com` produce the same `question_key()`?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dns/session_01_walkthrough.py
```

The walkthrough prints one scenario per structural rule and shows that two spellings of the same name collapse to one key.

## Done When

The learner can say all of the following without looking at notes:

- "A DNS question is a (name, type, class) triple, not just a name."
- "Normalization makes different spellings compare equal before any lookup happens."
- "Validation rejects a malformed question before a single server is contacted."

## References

- RFC 1034 Section 3.1
- RFC 1035 Section 2.3.4
- RFC 1035 Section 4.1.2
