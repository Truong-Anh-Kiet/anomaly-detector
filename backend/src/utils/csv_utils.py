"""CSV parsing and validation utilities"""

import csv
import logging
from datetime import datetime
from typing import List, Tuple, Optional
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


class CSVValidationError(Exception):
    """CSV validation error"""
    pass


class CSVParser:
    """CSV file parser and validator"""

    REQUIRED_FIELDS = {"date", "category", "amount"}
    OPTIONAL_FIELDS = {"source"}
    DATE_FORMAT = "%Y-%m-%d"

    def __init__(self):
        self.errors = []
        self.warnings = []

    def parse_file(self, file_path: str) -> List[dict]:
        """
        Parse and validate CSV file.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            List of validated transaction dictionaries
            
        Raises:
            CSVValidationError: If validation fails
        """
        self.errors = []
        self.warnings = []

        if not Path(file_path).exists():
            raise CSVValidationError(f"File not found: {file_path}")

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            raise CSVValidationError(f"Failed to read CSV: {e}")

        # Check required columns
        missing_cols = self.REQUIRED_FIELDS - set(df.columns)
        if missing_cols:
            raise CSVValidationError(f"Missing required columns: {missing_cols}")

        # Validate and parse rows
        valid_rows = []
        for idx, row in df.iterrows():
            try:
                validated_row = self._validate_row(row, idx)
                if validated_row:
                    valid_rows.append(validated_row)
            except CSVValidationError as e:
                self.errors.append(f"Row {idx + 2}: {str(e)}")

        if self.errors:
            logger.warning(f"CSV validation errors:\n" + "\n".join(self.errors))

        logger.info(
            f"Parsed {len(valid_rows)} valid rows from {file_path} "
            f"({len(self.errors)} errors)"
        )

        return valid_rows

    def _validate_row(self, row: pd.Series, row_idx: int) -> Optional[dict]:
        """Validate a single CSV row"""
        # Validate date
        try:
            date_str = str(row["date"]).strip()
            date_obj = datetime.strptime(date_str, self.DATE_FORMAT)
        except ValueError:
            raise CSVValidationError(
                f"Invalid date format: '{row['date']}' (expected YYYY-MM-DD)"
            )

        # Check date not in future
        if date_obj.date() > datetime.utcnow().date():
            raise CSVValidationError(f"Date cannot be in future: {row['date']}")

        # Validate category
        category = str(row["category"]).strip()
        if not category or len(category) < 1:
            raise CSVValidationError("Category cannot be empty")

        # Validate amount
        try:
            amount = float(row["amount"])
            if amount <= 0:
                self.warnings.append(f"Row {row_idx + 2}: Amount <= 0")
        except (ValueError, TypeError):
            raise CSVValidationError(f"Invalid amount: '{row['amount']}'")

        # Optional source field
        source = row.get("source", "").strip() if "source" in row else None

        return {
            "date": date_obj.date(),
            "category": category,
            "amount": amount,
            "source": source,
        }

    def parse_string(self, csv_content: str) -> List[dict]:
        """
        Parse CSV from string content.
        
        Args:
            csv_content: CSV content as string
            
        Returns:
            List of validated transaction dictionaries
        """
        import io
        
        self.errors = []
        self.warnings = []

        try:
            df = pd.read_csv(io.StringIO(csv_content))
        except Exception as e:
            raise CSVValidationError(f"Failed to parse CSV: {e}")

        # Check required columns
        missing_cols = self.REQUIRED_FIELDS - set(df.columns)
        if missing_cols:
            raise CSVValidationError(f"Missing required columns: {missing_cols}")

        # Validate rows
        valid_rows = []
        for idx, row in df.iterrows():
            try:
                validated_row = self._validate_row(row, idx)
                if validated_row:
                    valid_rows.append(validated_row)
            except CSVValidationError as e:
                self.errors.append(f"Row {idx + 2}: {str(e)}")

        if self.errors:
            logger.warning(f"CSV parsing errors:\n" + "\n".join(self.errors))

        return valid_rows
