"""
Metrics port for observability instrumentation.

This port allows application services to record timing and metrics
without depending on infrastructure-specific implementations.
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Generator


class MetricsPort(ABC):
    """
    Port interface for metrics collection.

    Allows application services to instrument operations for observability
    without coupling to specific metrics implementations.
    """

    @abstractmethod
    @contextmanager
    def time_operation(self, operation_name: str) -> Generator[None, None, None]:
        """
        Context manager to time an operation.

        Records duration metrics and logs timing information.

        Args:
            operation_name: Name of the operation being timed (e.g., "cart_add_item")

        Usage:
            with metrics.time_operation("cart_add_item"):
                # perform the operation
                pass
        """
        pass


class NoOpMetrics(MetricsPort):
    """
    No-op implementation for testing or when metrics are disabled.
    """

    @contextmanager
    def time_operation(self, operation_name: str) -> Generator[None, None, None]:
        yield
