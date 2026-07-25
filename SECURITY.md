# Security policy

Snarky is a research prototype and has no supported public release yet. The
current `main` branch receives security fixes on a best-effort basis.

## Reporting a vulnerability

Use GitHub private vulnerability reporting for this repository when available.
Include:

- the affected commit or version;
- a minimal reproduction;
- expected and observed impact;
- whether untrusted rule text, YAML, Python integrations, or generated files
  are involved;
- any known mitigation.

If private reporting is unavailable, open a minimal issue asking the
maintainer to establish a private channel. Do not publish exploit details,
credentials, private corpora, or sensitive generated data in a public issue.

Ordinary correctness and performance defects can use the public issue tracker.

## Scope

The textual rule parser does not intentionally evaluate arbitrary Python.
Computed predicates and object codecs execute application-supplied Python and
must be treated as trusted extensions. YAML, third-party corpora, MusicXML,
MIDI, and serialized research artifacts should be treated as untrusted input
when they do not originate from the current checkout.

Security fixes may change experimental APIs immediately. Stable-core changes
follow the compatibility policy when a safe deprecation period is possible.
