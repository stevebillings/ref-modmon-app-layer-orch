from dataclasses import fields
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


def to_dict(obj: Any) -> Any:
    """
    Recursively convert dataclasses to dictionaries for JSON serialization.

    Handles:
    - Dataclasses (converted to dict)
    - Lists (each element converted)
    - UUIDs and dates (converted to strings)
    - Decimals (converted to strings to preserve precision)
    - Other types passed through unchanged
    """
    if obj is None:
        return None

    if hasattr(obj, "__dataclass_fields__"):
        return {
            field.name: to_dict(getattr(obj, field.name))
            for field in fields(obj)
            if not field.name.startswith("_")  # Exclude private fields
        }

    if isinstance(obj, list):
        return [to_dict(item) for item in obj]

    if isinstance(obj, UUID):
        return str(obj)

    if isinstance(obj, (date, datetime)):
        return obj.isoformat()

    if isinstance(obj, Decimal):
        return str(obj)

    return obj
