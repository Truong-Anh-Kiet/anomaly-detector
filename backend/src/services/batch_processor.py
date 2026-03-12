"""Batch processing service for CSV import and anomaly detection"""

import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.config import get_settings
from src.database import Base, SessionLocal, engine
from src.ml.anomaly_model import AnomalyModel
from src.models import Category, Transaction
from src.services.anomaly_detector import AnomalyDetectionService
from src.utils.csv_utils import CSVParser

logger = logging.getLogger(__name__)


class BatchProcessorService:
    """Batch processing for CSV import and anomaly detection"""

    def __init__(self, model: AnomalyModel):
        self.model = model
        self.settings = get_settings()
        self.csv_parser = CSVParser()
        self.anomaly_detector = AnomalyDetectionService(model)
        self.scheduler = BackgroundScheduler()
        self.last_batch_status = None

    def initialize_scheduler(self):
        """Initialize APScheduler for daily batch jobs"""
        if self.scheduler.running:
            return

        # Add daily batch job
        trigger = CronTrigger(
            hour=self.settings.batch_job_hour,
            minute=self.settings.batch_job_minute,
            timezone="UTC",
        )
        self.scheduler.add_job(
            self.process_batch,
            trigger=trigger,
            id="daily_batch_anomaly_detection",
            name="Daily Anomaly Detection Batch",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info(
            f"Batch scheduler started (daily at "
            f"{self.settings.batch_job_hour:02d}:{self.settings.batch_job_minute:02d} UTC)"
        )

    def shutdown_scheduler(self):
        """Shutdown scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Batch scheduler stopped")

    def process_batch(
        self, csv_file_path: str | None = None, retry_count: int = 0
    ) -> dict:
        """
        Process batch: import CSV, detect anomalies, persist results.

        Implements auto-retry with exponential backoff on failure.

        Args:
            csv_file_path: Path to CSV file (if None, uses configured path)
            retry_count: Current retry attempt

        Returns:
            Status dictionary with processing results
        """
        db = SessionLocal()
        try:
            logger.info(f"Starting batch processing (attempt {retry_count + 1})")

            # Step 1: Initialize database
            Base.metadata.create_all(bind=engine)
            logger.info("Database schema initialized")

            # Step 2: Parse CSV
            csv_path = csv_file_path or self._get_csv_path()
            transactions_data = self.csv_parser.parse_file(csv_path)

            if not transactions_data:
                logger.warning("No valid transactions found in CSV")
                return self._batch_status("completed", 0, 0)

            # Step 3: Insert transactions
            imported_transactions = self._import_transactions(
                db, transactions_data
            )
            logger.info(f"Imported {len(imported_transactions)} transactions")

            # Step 4: Detect anomalies
            results_with_severity = self.anomaly_detector.detect_anomalies(
                db, imported_transactions, model_version="1.0.0"
            )

            # Step 5: Persist results
            anomaly_count = 0
            for result in results_with_severity:
                try:
                    db.add(result)
                    if result.result.value == "Anomaly":
                        anomaly_count += 1
                except IntegrityError:
                    # Result already exists, skip
                    db.rollback()
                    continue

            db.commit()
            logger.info(f"Detected and persisted {anomaly_count} anomalies")

            status = self._batch_status(
                "completed", len(imported_transactions), anomaly_count
            )
            self.last_batch_status = status
            return status

        except Exception as e:
            logger.error(f"Batch processing error: {e}", exc_info=True)
            db.rollback()

            # Retry logic
            if retry_count < 2:
                import time
                backoff_seconds = 2 ** retry_count  # Exponential backoff
                logger.info(f"Retrying batch in {backoff_seconds} seconds...")
                time.sleep(backoff_seconds)
                return self.process_batch(csv_file_path, retry_count + 1)

            # Final failure
            status = self._batch_status("failed", 0, 0, error=str(e))
            self.last_batch_status = status
            return status

        finally:
            db.close()

    def _import_transactions(
        self, db: Session, transactions_data: list[dict]
    ) -> list[Transaction]:
        """
        Import transaction records from parsed CSV data.

        Implements duplicate detection by (date, category, amount).
        """
        imported = []

        for data in transactions_data:
            # Check for duplicate (date, category, amount)
            existing = (
                db.query(Transaction)
                .filter(
                    Transaction.date == data["date"],
                    Transaction.category == data["category"],
                    Transaction.amount == data["amount"],
                )
                .first()
            )

            if existing:
                logger.debug(
                    f"Duplicate transaction skipped: "
                    f"{data['date']} {data['category']} {data['amount']}"
                )
                continue

            # Ensure category exists
            category = (
                db.query(Category)
                .filter(Category.name == data["category"])
                .first()
            )
            if not category:
                # Auto-create category if it doesn't exist
                category = Category(name=data["category"])
                db.add(category)
                db.commit()

            # Create transaction
            transaction = Transaction(
                date=data["date"],
                category=data["category"],
                amount=data["amount"],
                source=data.get("source"),
            )
            db.add(transaction)
            db.commit()
            imported.append(transaction)

        return imported

    def _get_csv_path(self) -> str:
        """Get CSV file path from configuration"""
        # In production, this would import from a data source
        # For now, return a default path
        return "./data/transactions.csv"

    def _batch_status(
        self,
        status: str,
        transactions_processed: int = 0,
        anomalies_detected: int = 0,
        error: str | None = None,
    ) -> dict:
        """Create batch status object"""
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "transactions_processed": transactions_processed,
            "anomalies_detected": anomalies_detected,
            "error": error,
        }

    def get_last_batch_status(self) -> dict | None:
        """Get status of last batch run"""
        return self.last_batch_status
