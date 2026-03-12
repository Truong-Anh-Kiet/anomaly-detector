"""Monitoring and performance observability service"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Single performance measurement"""

    endpoint: str
    method: str
    duration_ms: float
    status_code: int
    timestamp: datetime
    user_id: str | None = None
    error: str | None = None


class PerformanceMonitor:
    """Tracks API endpoint performance metrics"""

    def __init__(self, window_size: int = 1000):
        """
        Initialize monitor.

        Args:
            window_size: Number of recent metrics to keep in memory
        """
        self.metrics: list[PerformanceMetric] = []
        self.window_size = window_size
        self._lock = None  # For thread-safety in production

    def record_metric(
        self,
        endpoint: str,
        method: str,
        duration_ms: float,
        status_code: int,
        user_id: str | None = None,
        error: str | None = None,
    ) -> None:
        """Record a single API call metric"""
        metric = PerformanceMetric(
            endpoint=endpoint,
            method=method,
            duration_ms=duration_ms,
            status_code=status_code,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            error=error,
        )

        self.metrics.append(metric)

        # Keep only recent metrics
        if len(self.metrics) > self.window_size:
            self.metrics = self.metrics[-self.window_size :]

        if error:
            logger.warning(
                f"Slow/Error: {method} {endpoint} took {duration_ms:.2f}ms, "
                f"status={status_code}, error={error}"
            )

    def get_endpoint_stats(
        self, endpoint: str = None, minutes: int = 60
    ) -> dict:
        """
        Get aggregated statistics for endpoint(s).

        Args:
            endpoint: Specific endpoint to filter (None = all)
            minutes: Time window to consider

        Returns:
            Dictionary with aggregated metrics
        """
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)

        relevant_metrics = [
            m
            for m in self.metrics
            if m.timestamp >= cutoff and (endpoint is None or m.endpoint == endpoint)
        ]

        if not relevant_metrics:
            return {
                "endpoint": endpoint,
                "count": 0,
                "avg_duration_ms": 0,
                "min_duration_ms": 0,
                "max_duration_ms": 0,
                "error_rate": 0,
                "p95_duration_ms": 0,
            }

        durations = [m.duration_ms for m in relevant_metrics]
        errors = [m for m in relevant_metrics if m.error or m.status_code >= 400]

        # Calculate percentile
        durations_sorted = sorted(durations)
        p95_idx = int(len(durations_sorted) * 0.95)
        p95 = durations_sorted[p95_idx] if p95_idx < len(durations_sorted) else 0

        return {
            "endpoint": endpoint,
            "count": len(relevant_metrics),
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "error_rate": len(errors) / len(relevant_metrics) if relevant_metrics else 0,
            "p95_duration_ms": p95,
            "window_minutes": minutes,
        }

    def get_slowest_endpoints(self, limit: int = 10, minutes: int = 60) -> list[dict]:
        """Get slowest endpoints by average duration"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        relevant_metrics = [m for m in self.metrics if m.timestamp >= cutoff]

        # Group by endpoint
        by_endpoint = defaultdict(list)
        for m in relevant_metrics:
            by_endpoint[m.endpoint].append(m.duration_ms)

        # Calculate averages and sort
        stats = [
            {
                "endpoint": ep,
                "avg_duration_ms": sum(durations) / len(durations),
                "count": len(durations),
            }
            for ep, durations in by_endpoint.items()
        ]

        return sorted(
            stats, key=lambda x: x["avg_duration_ms"], reverse=True
        )[:limit]

    def get_error_summary(self, minutes: int = 60) -> dict:
        """Get summary of errors in time window"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        relevant_metrics = [m for m in self.metrics if m.timestamp >= cutoff]

        errors_by_endpoint = defaultdict(list)
        for m in relevant_metrics:
            if m.error or m.status_code >= 400:
                errors_by_endpoint[m.endpoint].append(
                    {
                        "status_code": m.status_code,
                        "error": m.error,
                        "timestamp": m.timestamp.isoformat(),
                    }
                )

        return {
            "total_errors": sum(len(e) for e in errors_by_endpoint.values()),
            "endpoints_with_errors": len(errors_by_endpoint),
            "errors_by_endpoint": dict(errors_by_endpoint),
            "window_minutes": minutes,
        }


class HealthChecker:
    """System health status checks"""

    def __init__(self):
        self.checks: dict[str, bool] = {
            "database": True,
            "ml_model": True,
            "cache": True,
            "external_api": True,
        }
        self.last_check = {}

    def set_status(self, component: str, healthy: bool):
        """Update health status of a component"""
        self.checks[component] = healthy
        self.last_check[component] = datetime.utcnow()
        if not healthy:
            logger.error(f"Health check failed for {component}")

    def is_healthy(self) -> bool:
        """Check if all critical components are healthy"""
        critical = ["database", "ml_model"]
        return all(self.checks.get(c, False) for c in critical)

    def get_status(self) -> dict:
        """Get full health status"""
        return {
            "healthy": self.is_healthy(),
            "components": self.checks,
            "last_checked": {
                k: v.isoformat() for k, v in self.last_check.items()
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    def check_database(self, db_session) -> bool:
        """Perform database health check"""
        try:
            # Simple query to verify DB connection
            db_session.execute("SELECT 1")
            self.set_status("database", True)
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            self.set_status("database", False)
            return False

    def check_ml_model(self, ml_service) -> bool:
        """Perform ML model health check"""
        try:
            # Simple inference test
            if hasattr(ml_service, "is_loaded") and ml_service.is_loaded():
                self.set_status("ml_model", True)
                return True
            else:
                self.set_status("ml_model", False)
                return False
        except Exception as e:
            logger.error(f"ML model health check failed: {e}")
            self.set_status("ml_model", False)
            return False


class MetricsCollector:
    """Collect and aggregate system metrics"""

    def __init__(self):
        self.counters: dict[str, int] = defaultdict(int)
        self.gauges: dict[str, float] = {}
        self.histograms: dict[str, list[float]] = defaultdict(list)

    def increment_counter(self, name: str, value: int = 1):
        """Increment a counter metric"""
        self.counters[name] += value

    def set_gauge(self, name: str, value: float):
        """Set a gauge to a specific value"""
        self.gauges[name] = value

    def record_histogram(self, name: str, value: float):
        """Record a value in a histogram"""
        self.histograms[name].append(value)

    def get_metrics(self) -> dict:
        """Get all collected metrics"""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                k: {
                    "count": len(v),
                    "min": min(v) if v else 0,
                    "max": max(v) if v else 0,
                    "avg": sum(v) / len(v) if v else 0,
                }
                for k, v in self.histograms.items()
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    def reset(self):
        """Reset all metrics"""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
