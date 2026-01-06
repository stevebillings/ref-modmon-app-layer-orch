# Cross-Bounded Context Communication

## Status

Future consideration - not yet implemented. The application currently has a single bounded context.

## Decision

When the application grows to require multiple bounded contexts, use **Stateless Model Translation (Anti-Corruption Layer)** as the default communication pattern.

## Context

This decision is informed by the constraint that the team size is approximately 3 developers. The chosen approach must balance architectural correctness with operational simplicity.

### Patterns Considered

| Pattern | Complexity | When to Use |
|---------|------------|-------------|
| Stateless ACL | Low | Default starting point |
| Stateful Model Translation | Medium | Performance/availability requirements |
| Outbox Pattern | Medium-High | Async messaging with delivery guarantees |
| Saga Pattern | High | Unavoidable distributed transactions |

### Why Stateless ACL

1. **Minimal infrastructure** - No additional databases, message brokers, or background workers
2. **Easy to reason about** - Translation happens synchronously at the boundary
3. **Easy to debug** - Stack traces are straightforward; no async gaps
4. **Low operational burden** - Nothing extra to monitor or maintain

## Implementation Approach

When a second bounded context is introduced, implement the ACL as follows:

### Directory Structure

```
backend/
  domain/
    context_a/           # First bounded context
      models.py
      services.py
      acl/               # Anti-Corruption Layer for consuming from other contexts
        context_b_translator.py
    context_b/           # Second bounded context
      models.py
      services.py
      acl/
        context_a_translator.py
```

### ACL Responsibilities

The Anti-Corruption Layer should:

1. **Translate external models** - Convert foreign bounded context models into the local ubiquitous language
2. **Isolate the domain** - Prevent foreign concepts from leaking into the domain model
3. **Adapt interfaces** - Provide a clean interface that matches local domain expectations

### Example Implementation

```python
# In context_a/acl/context_b_translator.py

from dataclasses import dataclass
from domain.context_b.models import ExternalProduct  # Foreign model

@dataclass
class LocalProductReference:
    """Local representation of a product from Context B."""
    product_id: str
    display_name: str
    is_available: bool

class ContextBTranslator:
    """Translates Context B models into Context A's ubiquitous language."""

    def __init__(self, context_b_repository):
        self._repository = context_b_repository

    def get_product_reference(self, product_id: str) -> LocalProductReference:
        """Fetch and translate a product from Context B."""
        external_product: ExternalProduct = self._repository.get_by_id(product_id)

        return LocalProductReference(
            product_id=external_product.id,
            display_name=self._translate_name(external_product),
            is_available=external_product.status == "ACTIVE"
        )

    def _translate_name(self, product: ExternalProduct) -> str:
        """Translate product naming convention to local convention."""
        # Context B uses SKU-based names; Context A uses display names
        return product.display_title or product.sku
```

### Integration with Hexagonal Architecture

The ACL fits into the existing hexagonal architecture as an **adapter** on the infrastructure layer that the domain consumes through a **port**:

```python
# Port (in domain layer)
class ProductReferencePort(Protocol):
    def get_product_reference(self, product_id: str) -> LocalProductReference:
        ...

# Adapter (in infrastructure layer, uses ACL)
class ContextBProductAdapter:
    def __init__(self, translator: ContextBTranslator):
        self._translator = translator

    def get_product_reference(self, product_id: str) -> LocalProductReference:
        return self._translator.get_product_reference(product_id)
```

## Evolution Path

If requirements change, consider these progressions:

1. **Add caching** to the ACL if repeated calls cause performance issues
2. **Introduce async messaging** with the Outbox pattern if eventual consistency is acceptable and you need guaranteed delivery
3. **Implement Sagas** only when distributed transactions are unavoidable

Each step up adds operational complexity and should be justified by concrete requirements.

## References

- Khononov, V. (2021). *Learning Domain-Driven Design*. O'Reilly Media. Chapter 9: Communication Patterns.
- Evans, E. (2003). *Domain-Driven Design: Tackling Complexity in the Heart of Software*. Addison-Wesley.
