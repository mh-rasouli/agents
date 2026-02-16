"""Google Sheets client for reading brand data."""

import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class GoogleSheetsClient:
    """Client for interacting with Google Sheets API."""

    def __init__(self, credentials_path: str):
        """Initialize Google Sheets client.

        Args:
            credentials_path: Path to service account JSON credentials file
        """
        self.credentials_path = credentials_path
        self.client = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Sheets API using service account."""
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=scopes
            )

            self.client = gspread.authorize(credentials)
            logger.info("[OK] Successfully authenticated with Google Sheets API")

        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets: {e}")
            raise

    def get_brands_from_sheet(
        self,
        sheet_id: str,
        worksheet_name: str = None,
        brand_column: str = "A",
        website_column: str = "B",
        parent_column: str = "C",
        start_row: int = 2
    ) -> List[Dict[str, str]]:
        """Read brands from Google Sheet.

        Args:
            sheet_id: Google Sheet ID
            worksheet_name: Name of worksheet (if None, uses first sheet)
            brand_column: Column containing brand names (default: A)
            website_column: Column containing websites (default: B)
            parent_column: Column containing parent company names (default: C)
            start_row: Row to start reading from (default: 2, skipping header)

        Returns:
            List of brand dictionaries with name, website, and parent company
        """
        try:
            # Open spreadsheet
            spreadsheet = self.client.open_by_key(sheet_id)
            logger.info(f"[OK] Opened spreadsheet: {spreadsheet.title}")

            # Get worksheet
            if worksheet_name:
                worksheet = spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = spreadsheet.get_worksheet(0)  # First sheet

            logger.info(f"[OK] Reading from worksheet: {worksheet.title}")

            # Get all values
            all_values = worksheet.get_all_values()

            if len(all_values) < start_row:
                logger.warning("No data found in sheet")
                return []

            # Parse brands
            brands = []
            brand_col_idx = ord(brand_column.upper()) - ord('A')
            website_col_idx = ord(website_column.upper()) - ord('A')
            parent_col_idx = ord(parent_column.upper()) - ord('A')

            for row_idx, row in enumerate(all_values[start_row - 1:], start=start_row):
                # Get brand name
                brand_name = row[brand_col_idx].strip() if len(row) > brand_col_idx else ""

                if not brand_name:
                    continue  # Skip empty rows

                # Get website (optional)
                website = row[website_col_idx].strip() if len(row) > website_col_idx else None
                if website and not website.startswith("http"):
                    website = None

                # Get parent company (optional)
                parent = row[parent_col_idx].strip() if len(row) > parent_col_idx else None

                brands.append({
                    "brand_name": brand_name,
                    "website": website,
                    "parent_company": parent,
                    "row_number": row_idx
                })

            logger.info(f"[OK] Read {len(brands)} brands from sheet")
            return brands

        except Exception as e:
            logger.error(f"Failed to read brands from sheet: {e}")
            raise

    def update_status(
        self,
        sheet_id: str,
        row_number: int,
        status_column: str = "D",
        status: str = "Completed"
    ):
        """Update processing status in Google Sheet.

        Args:
            sheet_id: Google Sheet ID
            row_number: Row number to update
            status_column: Column for status updates (default: D)
            status: Status message to write
        """
        try:
            spreadsheet = self.client.open_by_key(sheet_id)
            worksheet = spreadsheet.get_worksheet(0)

            # Convert column letter to cell reference
            cell = f"{status_column}{row_number}"
            worksheet.update(cell, status)

            logger.info(f"[OK] Updated status for row {row_number}: {status}")

        except Exception as e:
            logger.error(f"Failed to update status: {e}")

    def write_output_paths(
        self,
        sheet_id: str,
        row_number: int,
        output_paths: Dict[str, str],
        start_column: str = "E"
    ):
        """Write output file paths to Google Sheet.

        Args:
            sheet_id: Google Sheet ID
            row_number: Row number to update
            output_paths: Dictionary of output format -> file path
            start_column: Starting column for output paths (default: E)
        """
        try:
            spreadsheet = self.client.open_by_key(sheet_id)
            worksheet = spreadsheet.get_worksheet(0)

            # Prepare values to write
            values = []
            for format_type in ["txt", "json", "csv", "md"]:
                path = output_paths.get(format_type, "")
                values.append(path)

            # Write values starting from start_column
            start_col_idx = ord(start_column.upper()) - ord('A')
            range_notation = f"{start_column}{row_number}:{chr(ord(start_column) + len(values) - 1)}{row_number}"

            worksheet.update(range_notation, [values])
            logger.info(f"[OK] Wrote output paths for row {row_number}")

        except Exception as e:
            logger.error(f"Failed to write output paths: {e}")
