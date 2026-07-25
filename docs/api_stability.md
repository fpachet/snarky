# API stability

Snarky separates its public Python surface into four stability levels. The
machine-readable lists live in `snarky.api_stability`.

## Stable core

The stable core contains the terms, facts, rules, actions, parser entry points,
forward engine, sessions, and result types needed by most users. It is the only
surface exported by:

```python
from snarky import *
```

Stable names remain available from the package root and follow the
compatibility policy in [versioning.md](versioning.md).

## Advanced API

Advanced names expose search policies, propagation state, low-level
instantiation strategies, metrics, and extension points. They are public and
documented, but applications should import them from their defining modules:

```python
from snarky.choice import MRVChoicePolicy
from snarky.instantiation import SemiNaiveInstantiationStrategy
from snarky.propagation import DomainStore
```

## Integration API

Integration names adapt Snarky to external object models. They should be
imported from `snarky.integrations` or a submodule, for example:

```python
from snarky.integrations.objects import FactCodec
```

Compatibility can depend on the corresponding optional integration.

## Experimental API

Experimental names represent active research, including adaptive
instantiation and specialized constraint propagation. Their signatures and
behavior may evolve between minor releases while Snarky is pre-1.0. They
should be imported from their defining modules.

## Top-level transition

Before version 0.1.0, the package root re-exported every public implementation
type. Version 0.1.0 narrows `snarky.__all__` to the stable core so that
wildcard imports have a meaningful contract.

Explicit historical imports such as:

```python
from snarky import MRVChoicePolicy
```

continue to work throughout the 0.1 series. New code should use the defining
module for advanced, integration, and experimental names. Any future removal
of a historical root alias will be announced in the changelog, deprecated no
earlier than 0.2.0, and removed no earlier than 0.3.0.

The exact categories can be inspected without duplicating this document:

```python
from snarky.api_stability import (
    ADVANCED_API,
    EXPERIMENTAL_API,
    INTEGRATION_API,
    STABLE_CORE_API,
)
```

