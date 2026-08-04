"""
Date logic for calculating which dates to copy
Handles today, backdated scenarios, and path generation
"""

from datetime import datetime, timedelta
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class DateLogic:
    """Calculate dates to copy based on various scenarios"""

    # Date format in NAS path: YYYY/MMDD (e.g., 2024/0804)
    NAS_DATE_FORMAT = '%Y/%m%d'

    @staticmethod
    def get_today() -> str:
        """
        Get today's date in NAS format (YYYY/MMDD)

        Returns:
            str: Date in format YYYY/MMDD (e.g., '2024/0804')
        """
        return datetime.now().strftime(DateLogic.NAS_DATE_FORMAT)

    @staticmethod
    def get_date(year: int, month: int, day: int) -> str:
        """
        Get specific date in NAS format

        Args:
            year: Year (e.g., 2024)
            month: Month (1-12)
            day: Day (1-31)

        Returns:
            str: Date in format YYYY/MMDD (e.g., '2024/0804')

        Raises:
            ValueError: If date is invalid
        """
        try:
            date_obj = datetime(year, month, day)
            return date_obj.strftime(DateLogic.NAS_DATE_FORMAT)
        except ValueError as e:
            logger.error(f'Invalid date: {year}-{month:02d}-{day:02d}')
            raise ValueError(f'Invalid date: {year}-{month:02d}-{day:02d}') from e

    @staticmethod
    def get_yesterdays_date() -> str:
        """Get yesterday's date in NAS format"""
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.strftime(DateLogic.NAS_DATE_FORMAT)

    @staticmethod
    def get_date_range(start_date: str, end_date: str) -> List[str]:
        """
        Get list of dates between start and end (inclusive)

        Args:
            start_date: Date in format YYYY/MMDD
            end_date: Date in format YYYY/MMDD

        Returns:
            List[str]: List of dates in YYYY/MMDD format

        Example:
            >>> dates = get_date_range('2024/0801', '2024/0805')
            >>> dates
            ['2024/0801', '2024/0802', '2024/0803', '2024/0804', '2024/0805']
        """
        start = datetime.strptime(start_date, DateLogic.NAS_DATE_FORMAT)
        end = datetime.strptime(end_date, DateLogic.NAS_DATE_FORMAT)

        dates = []
        current = start
        while current <= end:
            dates.append(current.strftime(DateLogic.NAS_DATE_FORMAT))
            current += timedelta(days=1)

        return dates

    @staticmethod
    def get_last_n_days(n: int) -> List[str]:
        """
        Get last N days including today

        Args:
            n: Number of days to include (e.g., 7 for last 7 days)

        Returns:
            List[str]: List of dates in YYYY/MMDD format, most recent first

        Example:
            >>> dates = get_last_n_days(3)
            >>> # Returns [today, yesterday, 2 days ago]
        """
        today = datetime.now()
        dates = []

        for i in range(n):
            date = today - timedelta(days=i)
            dates.append(date.strftime(DateLogic.NAS_DATE_FORMAT))

        return dates

    @staticmethod
    def is_valid_nas_date_format(date_str: str) -> bool:
        """
        Check if date is in valid NAS format (YYYY/MMDD)

        Args:
            date_str: Date string to validate

        Returns:
            bool: True if valid format
        """
        try:
            datetime.strptime(date_str, DateLogic.NAS_DATE_FORMAT)
            return True
        except ValueError:
            return False

    @staticmethod
    def get_last_business_day() -> str:
        """
        Get last business day (excludes weekends)

        Returns:
            str: Date in format YYYY/MMDD
        """
        yesterday = datetime.now() - timedelta(days=1)

        # If yesterday is Saturday (5), go back 1 day
        # If yesterday is Sunday (6), go back 2 days
        while yesterday.weekday() > 4:  # 0=Monday, 4=Friday, 5=Saturday, 6=Sunday
            yesterday -= timedelta(days=1)

        return yesterday.strftime(DateLogic.NAS_DATE_FORMAT)

    @staticmethod
    def get_last_month_end() -> str:
        """
        Get last day of previous month

        Returns:
            str: Date in format YYYY/MMDD

        Example:
            >>> # If today is 2024-08-15
            >>> date = get_last_month_end()
            >>> date
            '2024/0731'  # Last day of July 2024
        """
        today = datetime.now()
        first_day_this_month = today.replace(day=1)
        last_day_prev_month = first_day_this_month - timedelta(days=1)
        return last_day_prev_month.strftime(DateLogic.NAS_DATE_FORMAT)

    @staticmethod
    def parse_nas_date(date_str: str) -> datetime:
        """
        Parse NAS date format to datetime object

        Args:
            date_str: Date in format YYYY/MMDD

        Returns:
            datetime: Parsed datetime object
        """
        return datetime.strptime(date_str, DateLogic.NAS_DATE_FORMAT)


class DataSyncDateCalculator:
    """
    High-level calculator for determining which dates to copy
    based on common scenarios
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_dates_to_copy(
        self,
        scenario: str = 'daily',
        custom_date: Optional[str] = None,
        days_back: int = 0
    ) -> List[str]:
        """
        Calculate which dates need to be copied

        Args:
            scenario: One of:
                - 'daily': Copy today's data (default)
                - 'backdated': Copy specific date (requires custom_date)
                - 'range': Copy last N days (requires days_back)
                - 'weekly': Copy last 7 days
                - 'monthly': Copy all days from previous month end
                - 'custom': Use custom_date

            custom_date: Date in YYYY/MMDD format for backdated/custom scenarios
            days_back: Number of days to look back (for 'range' scenario)

        Returns:
            List[str]: List of dates to copy

        Raises:
            ValueError: If parameters are invalid for scenario
        """
        if scenario == 'daily':
            return [DateLogic.get_today()]

        elif scenario == 'backdated':
            if not custom_date:
                raise ValueError("'backdated' scenario requires custom_date parameter")
            if not DateLogic.is_valid_nas_date_format(custom_date):
                raise ValueError(f"Invalid date format: {custom_date}. Expected YYYY/MMDD")
            return [custom_date]

        elif scenario == 'range':
            if days_back < 1:
                raise ValueError("'range' scenario requires days_back >= 1")
            return DateLogic.get_last_n_days(days_back)

        elif scenario == 'weekly':
            return DateLogic.get_last_n_days(7)

        elif scenario == 'monthly':
            # Get last day of previous month and all days before today in current month
            last_month_end = DateLogic.get_last_month_end()
            today = DateLogic.get_today()
            return DateLogic.get_date_range(last_month_end, today)

        elif scenario == 'custom':
            if not custom_date:
                raise ValueError("'custom' scenario requires custom_date parameter")
            if not DateLogic.is_valid_nas_date_format(custom_date):
                raise ValueError(f"Invalid date format: {custom_date}. Expected YYYY/MMDD")
            return [custom_date]

        else:
            raise ValueError(
                f"Unknown scenario: {scenario}. "
                f"Valid options: daily, backdated, range, weekly, monthly, custom"
            )

    def get_summary(self, dates: List[str]) -> str:
        """
        Get human-readable summary of dates

        Args:
            dates: List of dates in YYYY/MMDD format

        Returns:
            str: Summary string
        """
        if not dates:
            return "No dates to copy"

        if len(dates) == 1:
            return f"Copying 1 date: {dates[0]}"

        if len(dates) <= 5:
            return f"Copying {len(dates)} dates: {', '.join(dates)}"

        return (
            f"Copying {len(dates)} dates: "
            f"{dates[0]} to {dates[-1]}"
        )
