import unittest
from datetime import datetime, timezone

from py_relative_time_delta.core import apply_phrase, PhraseError


class TestApplyPhrase(unittest.TestCase):
    def setUp(self):
        self.base = datetime(2024, 3, 13, 10, 30, 0, tzinfo=timezone.utc)

    def _result(self, phrase, dt=None):
        """Apply phrase and return the result's date + original time."""
        b = dt if dt is not None else self.base
        r = apply_phrase(b, phrase)
        return (r.year, r.month, r.day, r.hour, r.minute, r.second, r.tzinfo)

    # ------------------------------------------------------------------
    # Ordinal weekday in a named month
    # ------------------------------------------------------------------
    def test_third_wednesday_of_march(self):
        # March 2024 Wednesdays: 6, 13, 20, 27 → 3rd is 20th
        y, m, d, h, mi, s, tz = self._result("third Wednesday of March")
        self.assertEqual((y, m, d), (2024, 3, 20))
        self.assertEqual((h, mi, s), (10, 30, 0))
        self.assertIs(tz, timezone.utc)

    def test_first_monday_of_january(self):
        # Jan 2024 Mondays: 1, 8, 15, 22, 29
        y, m, d, *_ = self._result("first Monday of January")
        self.assertEqual((y, m, d), (2024, 1, 1))

    def test_fifth_monday_of_january(self):
        # Jan 2024 has 5 Mondays
        y, m, d, *_ = self._result("fifth Monday of January")
        self.assertEqual((y, m, d), (2024, 1, 29))

    # ------------------------------------------------------------------
    # Ordinal weekday using base month (no month named)
    # ------------------------------------------------------------------
    def test_second_friday_in_base_month(self):
        # March 2024 Fridays: 1, 8, 15, 22, 29
        y, m, d, *_ = self._result("second Friday")
        self.assertEqual((y, m, d), (2024, 3, 8))

    def test_first_monday_in_base_month(self):
        # March 2024 Mondays: 4, 11, 18, 25
        y, m, d, *_ = self._result("first Monday")
        self.assertEqual((y, m, d), (2024, 3, 4))

    # ------------------------------------------------------------------
    # Last weekday of a named month
    # ------------------------------------------------------------------
    def test_last_monday_of_march(self):
        y, m, d, *_ = self._result("last Monday of March")
        self.assertEqual((y, m, d), (2024, 3, 25))

    def test_last_sunday_of_february(self):
        # Feb 2024 Sundays: 4, 11, 18, 25
        y, m, d, *_ = self._result("last Sunday of February")
        self.assertEqual((y, m, d), (2024, 2, 25))

    # ------------------------------------------------------------------
    # Last weekday using base month (no month named)
    # ------------------------------------------------------------------
    def test_last_thursday_in_base_month(self):
        # March 2024 Thursdays: 7, 14, 21, 28
        y, m, d, *_ = self._result("last Thursday")
        self.assertEqual((y, m, d), (2024, 3, 28))

    # ------------------------------------------------------------------
    # Time and tz preservation across a month boundary
    # ------------------------------------------------------------------
    def test_time_preserved_when_crossing_month(self):
        base = datetime(2024, 1, 31, 9, 15, 42, 123456, tzinfo=timezone.utc)
        y, m, d, h, mi, s, tz = self._result("first Wednesday of March", base)
        self.assertEqual((y, m, d), (2024, 3, 6))
        self.assertEqual((h, mi, s), (9, 15, 42))
        self.assertIs(tz, timezone.utc)

    # ------------------------------------------------------------------
    # Case insensitivity and whitespace
    # ------------------------------------------------------------------
    def test_case_insensitive_and_whitespace(self):
        y, m, d, *_ = self._result("  THIRD  wednesday  of  MARCH  ")
        self.assertEqual((y, m, d), (2024, 3, 20))

    # ------------------------------------------------------------------
    # Edge case: fifth weekday that doesn't exist in a short month
    # ------------------------------------------------------------------
    def test_fifth_monday_of_february_raises(self):
        # Feb 2024 Mondays: 5, 12, 19, 26 → no 5th
        with self.assertRaises(PhraseError):
            apply_phrase(self.base, "fifth Monday of February")

    # ------------------------------------------------------------------
    # Edge case: ordinal out of range
    # ------------------------------------------------------------------
    def test_sixth_monday_raises(self):
        with self.assertRaises(PhraseError):
            apply_phrase(self.base, "sixth Monday of March")

    # ------------------------------------------------------------------
    # Error cases
    # ------------------------------------------------------------------
    def test_empty_phrase_raises(self):
        with self.assertRaises(PhraseError):
            apply_phrase(self.base, "")

    def test_whitespace_only_raises(self):
        with self.assertRaises(PhraseError):
            apply_phrase(self.base, "   ")

    def test_unknown_weekday_raises(self):
        with self.assertRaises(PhraseError):
            apply_phrase(self.base, "third Fundayday of March")

    def test_unknown_month_raises(self):
        with self.assertRaises(PhraseError):
            apply_phrase(self.base, "third Wednesday of Smarch")

    def test_garbled_phrase_raises(self):
        with self.assertRaises(PhraseError):
            apply_phrase(self.base, "the quick brown fox")

    def test_phrase_error_is_value_error(self):
        self.assertTrue(issubclass(PhraseError, ValueError))


if __name__ == "__main__":
    unittest.main()
