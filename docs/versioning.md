# Versioning and compatibility

Snarky follows Semantic Versioning, with the additional caution appropriate
to a pre-1.0 research package.

## Python API

- Patch releases fix defects and may improve performance without intentionally
  changing observable behavior.
- Minor releases may add stable features. Incompatible stable-core changes
  require a documented deprecation period spanning at least one minor release.
- Experimental APIs may change in a minor release and are identified in
  [api_stability.md](api_stability.md).
- Advanced extension points are public, but their internal performance
  characteristics are not compatibility guarantees.
- A 1.0 release will freeze the stable-core contract under normal Semantic
  Versioning rules.

Compatibility covers documented call signatures, import locations, return
types, deterministic ordering, and the semantics of facts, mutation,
refraction, checkpoints, and search results. Runtime performance is tested for
regressions but is not itself part of the semantic API.

## Rule language

The textual rule language is versioned with the package:

- existing valid rules must retain their meaning in patch releases;
- new unambiguous syntax may be added in minor releases;
- syntax removal or semantic reinterpretation requires a deprecation notice
  and a migration example;
- parser diagnostics may be clarified provided their documented error family
  remains stable.

Research syntax marked experimental can evolve in minor releases, but changes
must be recorded in the changelog.

## Serialized data

Serialized rule programs and project-specific YAML formats must include, or be
associated with, a schema version before they are presented as durable
interchange formats. Readers should accept older compatible schemas or fail
with a clear version error. Pickle output, internal checkpoints, cache files,
and benchmark result files are reproducible artifacts rather than stable
exchange formats.

## Deprecation process

A deprecation must:

1. be announced in `CHANGELOG.md`;
2. identify the supported replacement;
3. remain functional for at least one minor release;
4. emit a targeted warning when that can be done without disrupting hot paths;
5. be removed only in a later minor release before 1.0, or a major release
   after 1.0.

