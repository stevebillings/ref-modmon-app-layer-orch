"""
Simple in-memory metrics collection for observability.

Provides counters and gauges that can be exposed via a Prometheus-compatible endpoint.
For production use, consider using prometheus_client library instead.
"""

import threading
from collections import defaultdict
from typing import Dict


class Metrics:
    """
    Thread-safe metrics collector.

    Tracks counters and gauges for application observability.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}

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
            for key, value in sorted(self._counters.items()):
                lines.append(f"{key} {value}")

            # Export gauges
            for key, value in sorted(self._gauges.items()):
                lines.append(f"{key} {value}")

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
