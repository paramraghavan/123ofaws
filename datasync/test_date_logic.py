"""
Unit tests for date_logic module
"""

import unittest
from datetime import datetime, timedelta
from date_logic import DateLogic, DataSyncDateCalculator


class TestDateLogic(unittest.TestCase):
    """Test DateLogic class"""

    def test_today_format(self):
        """Test that today's date is in correct format"""
        today = DateLogic.get_today()
        self.assertRegex(today, r'^\d{4}/\d{4}$')  # YYYY/MMDD format

        # Verify it's parseable
        parsed = DateLogic.parse_nas_date(today)
        self.assertIsInstance(parsed, datetime)

    def test_get_specific_date(self):
        """Test getting specific date"""
        date = DateLogic.get_date(2024, 8, 4)
        self.assertEqual(date, '2024/0804')

    def test_invalid_date(self):
        """Test that invalid dates raise ValueError"""
        with self.assertRaises(ValueError):
            DateLogic.get_date(2024, 2, 30)  # February 30th doesn't exist

    def test_yesterdays_date(self):
        """Test getting yesterday's date"""
        yesterday = DateLogic.get_yesterdays_date()
        expected = (datetime.now() - timedelta(days=1)).strftime('%Y/%m%d')
        self.assertEqual(yesterday, expected)

    def test_date_range(self):
        """Test date range generation"""
        dates = DateLogic.get_date_range('2024/0801', '2024/0805')
        expected = ['2024/0801', '2024/0802', '2024/0803', '2024/0804', '2024/0805']
        self.assertEqual(dates, expected)

    def test_last_n_days(self):
        """Test getting last N days"""
        dates = DateLogic.get_last_n_days(3)
        self.assertEqual(len(dates), 3)

        # First date should be today
        self.assertEqual(dates[0], DateLogic.get_today())

    def test_valid_date_format(self):
        """Test date format validation"""
        self.assertTrue(DateLogic.is_valid_nas_date_format('2024/0804'))
        self.assertFalse(DateLogic.is_valid_nas_date_format('2024-08-04'))
        self.assertFalse(DateLogic.is_valid_nas_date_format('2024/08/04'))

    def test_last_business_day(self):
        """Test last business day calculation"""
        last_business = DateLogic.get_last_business_day()
        # Should be a valid date
        self.assertRegex(last_business, r'^\d{4}/\d{4}$')

    def test_parse_date(self):
        """Test parsing date"""
        parsed = DateLogic.parse_nas_date('2024/0804')
        self.assertEqual(parsed.year, 2024)
        self.assertEqual(parsed.month, 8)
        self.assertEqual(parsed.day, 4)


class TestDataSyncDateCalculator(unittest.TestCase):
    """Test DataSyncDateCalculator class"""

    def setUp(self):
        self.calculator = DataSyncDateCalculator()

    def test_daily_scenario(self):
        """Test daily scenario returns today's date"""
        dates = self.calculator.calculate_dates_to_copy('daily')
        self.assertEqual(len(dates), 1)
        self.assertEqual(dates[0], DateLogic.get_today())

    def test_backdated_scenario(self):
        """Test backdated scenario with specific date"""
        dates = self.calculator.calculate_dates_to_copy(
            'backdated',
            custom_date='2024/0721'
        )
        self.assertEqual(dates, ['2024/0721'])

    def test_backdated_missing_date(self):
        """Test backdated scenario without date raises error"""
        with self.assertRaises(ValueError):
            self.calculator.calculate_dates_to_copy('backdated')

    def test_range_scenario(self):
        """Test range scenario"""
        dates = self.calculator.calculate_dates_to_copy('range', days_back=3)
        self.assertEqual(len(dates), 3)

    def test_range_invalid_days(self):
        """Test range with invalid days_back"""
        with self.assertRaises(ValueError):
            self.calculator.calculate_dates_to_copy('range', days_back=0)

    def test_weekly_scenario(self):
        """Test weekly scenario"""
        dates = self.calculator.calculate_dates_to_copy('weekly')
        self.assertEqual(len(dates), 7)

    def test_invalid_scenario(self):
        """Test invalid scenario raises error"""
        with self.assertRaises(ValueError):
            self.calculator.calculate_dates_to_copy('invalid_scenario')

    def test_summary_single_date(self):
        """Test summary for single date"""
        dates = ['2024/0804']
        summary = self.calculator.get_summary(dates)
        self.assertIn('1 date', summary)

    def test_summary_multiple_dates(self):
        """Test summary for multiple dates"""
        dates = ['2024/0801', '2024/0802', '2024/0803']
        summary = self.calculator.get_summary(dates)
        self.assertIn('3 dates', summary)


if __name__ == '__main__':
    unittest.main()
