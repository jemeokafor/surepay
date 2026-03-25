import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
import logging
from typing import Dict, Any, Optional
import time
import psutil
import os

# Configure Sentry
sentry_logging = LoggingIntegration(
    level=logging.INFO,        # Capture info and above as breadcrumbs
    event_level=logging.ERROR   # Send errors as events
)

def init_sentry(dsn: str, environment: str = "production"):
    """
    Initialize Sentry for error tracking and performance monitoring
    """
    if not dsn:
        logging.warning("Sentry DSN not provided, skipping initialization")
        return
    
    sentry_sdk.init(
        dsn=dsn,
        integrations=[
            sentry_logging,
        ],
        traces_sample_rate=1.0,  # Capture 100% of transactions for performance monitoring
        profiles_sample_rate=1.0,  # Capture 100% of profiles for performance monitoring
        environment=environment,
        release=os.environ.get("RELEASE", "unknown"),
    )
    logging.info("Sentry initialized successfully")

class PerformanceMonitor:
    """
    Performance monitoring for SurePay application
    """
    
    def __init__(self):
        self.metrics = {}
        
    def start_timer(self, operation_name: str) -> str:
        """
        Start timing an operation
        """
        timer_id = f"{operation_name}_{int(time.time() * 1000)}"
        self.metrics[timer_id] = {
            "operation": operation_name,
            "start_time": time.time(),
            "end_time": None,
            "duration": None
        }
        return timer_id
    
    def end_timer(self, timer_id: str) -> float:
        """
        End timing an operation and return duration
        """
        if timer_id in self.metrics:
            self.metrics[timer_id]["end_time"] = time.time()
            duration = self.metrics[timer_id]["end_time"] - self.metrics[timer_id]["start_time"]
            self.metrics[timer_id]["duration"] = duration
            return duration
        return 0.0
    
    def log_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """
        Log a custom metric
        """
        logging.info(f"Metric: {name} = {value}", extra=tags or {})
        
        # Send to Sentry as a custom measurement
        with sentry_sdk.push_scope() as scope:
            for key, val in (tags or {}).items():
                scope.set_tag(key, val)
            sentry_sdk.set_measurement(name, value)

def get_system_metrics() -> Dict[str, Any]:
    """
    Get system-level metrics
    """
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "network_io": psutil.net_io_counters()._asdict(),
    }

class BusinessAnalytics:
    """
    Business analytics tracking for SurePay
    """
    
    def __init__(self):
        self.transaction_count = 0
        self.payout_count = 0
        self.dispute_count = 0
        self.revenue = 0.0
    
    def track_transaction(self, amount: float, fee: float):
        """
        Track a successful transaction
        """
        self.transaction_count += 1
        self.revenue += fee
        logging.info(f"Transaction tracked: amount={amount}, fee={fee}")
        
        # Send to analytics
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("event_type", "transaction")
            sentry_sdk.set_measurement("transaction_amount", amount)
            sentry_sdk.set_measurement("transaction_fee", fee)
            sentry_sdk.capture_message("Transaction completed", level="info")
    
    def track_payout(self, amount: float):
        """
        Track a successful payout
        """
        self.payout_count += 1
        logging.info(f"Payout tracked: amount={amount}")
        
        # Send to analytics
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("event_type", "payout")
            sentry_sdk.set_measurement("payout_amount", amount)
            sentry_sdk.capture_message("Payout completed", level="info")
    
    def track_dispute(self, resolution: str):
        """
        Track a dispute resolution
        """
        self.dispute_count += 1
        logging.info(f"Dispute tracked: resolution={resolution}")
        
        # Send to analytics
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("event_type", "dispute")
            scope.set_tag("resolution", resolution)
            sentry_sdk.capture_message("Dispute resolved", level="info")
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """
        Get business analytics summary
        """
        return {
            "transactions": self.transaction_count,
            "payouts": self.payout_count,
            "disputes": self.dispute_count,
            "revenue": self.revenue,
            "timestamp": time.time()
        }

# Global instances
performance_monitor = PerformanceMonitor()
business_analytics = BusinessAnalytics()

def setup_monitoring(sentry_dsn: str = None, environment: str = "production"):
    """
    Setup complete monitoring system
    """
    # Initialize Sentry
    if sentry_dsn:
        init_sentry(sentry_dsn, environment)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logging.info("Monitoring system initialized")

def log_error(error: Exception, context: Dict[str, Any] = None):
    """
    Log an error with context
    """
    logging.error(f"Error occurred: {str(error)}", extra=context or {})
    
    # Send to Sentry
    with sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_extra(key, value)
        sentry_sdk.capture_exception(error)

def log_info(message: str, context: Dict[str, Any] = None):
    """
    Log an info message with context
    """
    logging.info(message, extra=context or {})
    
    # Send to Sentry as breadcrumb
    sentry_sdk.add_breadcrumb(
        category="info",
        message=message,
        level="info",
        data=context or {}
    )

# Alert system
class AlertSystem:
    """
    Alert system for critical events
    """
    
    def __init__(self):
        self.alerts = []
    
    def check_system_health(self):
        """
        Check system health and send alerts if needed
        """
        metrics = get_system_metrics()
        
        # Check CPU usage
        if metrics["cpu_percent"] > 90:
            self.send_alert("HIGH_CPU", f"CPU usage is {metrics['cpu_percent']}%", "critical")
        
        # Check memory usage
        if metrics["memory_percent"] > 90:
            self.send_alert("HIGH_MEMORY", f"Memory usage is {metrics['memory_percent']}%", "critical")
        
        # Check disk usage
        if metrics["disk_percent"] > 95:
            self.send_alert("HIGH_DISK", f"Disk usage is {metrics['disk_percent']}%", "critical")
    
    def send_alert(self, alert_type: str, message: str, severity: str = "info"):
        """
        Send an alert
        """
        alert = {
            "type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": time.time()
        }
        
        self.alerts.append(alert)
        logging.warning(f"Alert: {alert_type} - {message}")
        
        # Send to Sentry
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("alert_type", alert_type)
            scope.set_tag("severity", severity)
            sentry_sdk.capture_message(f"Alert: {message}", level="warning" if severity == "info" else "error")

# Global alert system
alert_system = AlertSystem()