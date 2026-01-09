"""
Simple in-memory metrics collection for observability.

Provides counters and gauges that can be exposed via a Prometheus-compatible endpoint.
For production use, consider using prometheus_client library instead.
"""

import logging
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from typing import Dict, Generator, List

from application.ports.metrics import MetricsPort

logger = logging.getLogger(__name__)


class Metrics:
    """
    Thread-safe metrics collector.

    Tracks counters, gauges, and histograms for application observability.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)

    def increment(self, name: str, value: int = 1, labels: Dict[str, str] | None = None) -> None:
        """Increment a counter metric."""
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] += value

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] | None = None) -> None:
        """Set a gauge metric to a specific value."""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value

    def get_counter(self, name: str, labels: Dict[str, str] | None = None) -> int:
        """Get current value of a counter."""
        key = self._make_key(name, labels)
        with self._lock:
            return self._counters.get(key, 0)

    def get_gauge(self, name: str, labels: Dict[str, str] | None = None) -> float:
        """Get current value of a gauge."""
        key = self._make_key(name, labels)
        with self._lock:
            return self._gauges.get(key, 0.0)

    def observe(self, name: str, value: float, labels: Dict[str, str] | None = None) -> None:
        """Record an observation for a histogram metric."""
        key = self._make_key(name, labels)
        with self._lock:
            self._histograms[key].append(value)

    def _make_key(self, name: str, labels: Dict[str, str] | None) -> str:
        """Create a unique key for a metric with labels."""
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def to_prometheus(self) -> str:
        """Export all metrics in Prometheus text format."""
        lines = []

        with self._lock:
            # Export counters
            for key, count_value in sorted(self._counters.items()):
                lines.append(f"{key} {count_value}")

            # Export gauges
            for key, gauge_value in sorted(self._gauges.items()):
                lines.append(f"{key} {gauge_value}")

            # Export histogram summaries (count, sum, avg, min, max)
            for key, values in sorted(self._histograms.items()):
                if values:
                    count = len(values)
                    total = sum(values)
                    avg = total / count
                    min_val = min(values)
                    max_val = max(values)
                    lines.append(f"{key}_count {count}")
                    lines.append(f"{key}_sum {total:.2f}")
                    lines.append(f"{key}_avg {avg:.2f}")
                    lines.append(f"{key}_min {min_val:.2f}")
                    lines.append(f"{key}_max {max_val:.2f}")

        return "\n".join(lines)


# Global metrics instance
_metrics = Metrics()


def get_metrics() -> Metrics:
    """Get the global metrics instance."""
    return _metrics


# Convenience functions for common metrics
def record_request(method: str, path: str, status_code: int) -> None:
    """Record an HTTP request."""
    _metrics.increment(
        "http_requests_total",
        labels={"method": method, "status": str(status_code)},
    )
    if status_code >= 500:
        _metrics.increment("http_errors_total", labels={"method": method})


def record_domain_event(event_type: str) -> None:
    """Record a domain event."""
    _metrics.increment("domain_events_total", labels={"type": event_type})


def record_order_created() -> None:
    """Record an order creation."""
    _metrics.increment("orders_created_total")


def record_cart_submitted() -> None:
    """Record a cart submission."""
    _metrics.increment("carts_submitted_total")


@contextmanager
def time_operation(operation_name: str) -> Generator[None, None, None]:
    """
    Context manager to time an operation and record metrics.

    Usage:
        with time_operation("cart_submission"):
            # do the operation
            pass

    Records duration in milliseconds to operation_duration_ms histogram.
    Also logs the timing with request correlation.
    """
    from infrastructure.django_app.request_context import get_request_id

    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        _metrics.observe(
            "operation_duration_ms",
            duration_ms,
            labels={"operation": operation_name},
        )
        _metrics.increment(
            "operations_total",
            labels={"operation": operation_name},
        )
        logger.info(
            f"Operation completed: {operation_name}",
            extra={
                "operation": operation_name,
                "duration_ms": round(duration_ms, 2),
                "request_id": get_request_id(),
            },
        )


def record_operation_timing(operation_name: str, duration_ms: float) -> None:
    """Record timing for an operation directly (alternative to context manager)."""
    _metrics.observe(
        "operation_duration_ms",
        duration_ms,
        labels={"operation": operation_name},
    )
    _metrics.increment(
        "operations_total",
        labels={"operation": operation_name},
    )


class DjangoMetricsAdapter(MetricsPort):
    """
    Django implementation of the MetricsPort interface.

    Uses the global metrics collector for recording operation timing.
    """

    @contextmanager
    def time_operation(self, operation_name: str) -> Generator[None, None, None]:
        """
        Context manager to time an operation and record metrics.

        Records duration in milliseconds to operation_duration_ms histogram.
        Also logs the timing with request correlation.
        """
        from infrastructure.django_app.request_context import get_request_id

        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.observe(
                "operation_duration_ms",
                duration_ms,
                labels={"operation": operation_name},
            )
            _metrics.increment(
                "operations_total",
                labels={"operation": operation_name},
            )
            logger.info(
                f"Operation completed: {operation_name}",
                extra={
                    "operation": operation_name,
                    "duration_ms": round(duration_ms, 2),
                    "request_id": get_request_id(),
                },
            )


# Singleton instance for dependency injection
_metrics_adapter: DjangoMetricsAdapter | None = None


def get_metrics_adapter() -> DjangoMetricsAdapter:
    """Get the singleton metrics adapter instance."""
    global _metrics_adapter
    if _metrics_adapter is None:
        _metrics_adapter = DjangoMetricsAdapter()
    return _metrics_adapter
