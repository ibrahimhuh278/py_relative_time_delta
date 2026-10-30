from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

ORDINALS = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
}


class PhraseError(ValueError):
    """Raised when a phrase cannot be parsed.

    Subclasses ValueError so that callers who only catch ValueError are
    unaffected.
    """


@dataclass(frozen=True)
class _OrdinalWeekdayInMonth:
    """e.g. 'third Wednesday of July' → ordinal=3, weekday=2, month=7.

    If month is None the phrase did not name a month (e.g. 'second Friday'),
    and the month is taken from the input datetime.
    """
    ordinal: int
    weekday: int
    month: Optional[int]


def _ordinal_weekday_in_month(
    base: date, ordinal: int, weekday: int, month: Optional[int]
) -> date:
    """Return the Nth occurrence of weekday in the given (or base) month.

    Raises PhraseError when ordinal is out of range for the month.
    """
    if ordinal < 1 or ordinal > 5:
        raise PhraseError(f"ordinal must be 1-5, got {ordinal}")
    m = month if month is not None else base.month
    cal = calendar.Calendar()
    matches = [
        d for d in cal.itermonthdates(base.year, m) if d.month == m and d.weekday() == weekday
    ]
    if ordinal > len(matches):
        raise PhraseError(
            f"there is no {ordinal_to_word(ordinal)} "
            f"{WEEKDAY_NAMES[weekday]} in {MONTH_NAMES[m]} {base.year}"
        )
    return matches[ordinal - 1]


@dataclass(frozen=True)
class _LastWeekdayInMonth:
    """e.g. 'last Monday of March' → weekday=0, month=3."""
    weekday: int
    month: Optional[int]


def _last_weekday_in_month(
    base: date, weekday: int, month: Optional[int]
) -> date:
    m = month if month is not None else base.month
    cal = calendar.Calendar()
    matches = [
        d for d in cal.itermonthdates(base.year, m) if d.month == m and d.weekday() == weekday
    ]
    if not matches:
        # Unreachable for any valid month/weekday combination, but defensive.
        raise PhraseError(f"no {WEEKDAY_NAMES[weekday]} in {MONTH_NAMES[m]} {base.year}")
    return matches[-1]


WEEKDAY_NAMES = {v: k.capitalize() for k, v in WEEKDAYS.items()}
MONTH_NAMES = {v: k.capitalize() for k, v in MONTHS.items()}


def ordinal_to_word(n: int) -> str:
    """1 → 'first', 2 → 'second', etc. for the five supported ordinals."""
    for word, num in ORDINALS.items():
        if num == n:
            return word
    return str(n)


def apply_phrase(base: datetime, phrase: str) -> datetime:
    """Apply a relative time phrase to *base* and return a new datetime.

    The time component (hour, minute, second, microsecond, tzinfo) of *base*
    is preserved unchanged; only the date is replaced.

    Supported forms:

    1. "<ordinal> <Weekday> of <Month>"
       e.g. "third Wednesday of March"
    2. "<ordinal> <Weekday>"
       e.g. "second Friday"
       (uses the month of *base*)
    3. "last <Weekday> of <Month>"
       e.g. "last Monday of March"
    4. "last <Weekday>"
       e.g. "last Thursday"
       (uses the month of *base*)

    All comparisons are case-insensitive and ignore leading/trailing
    whitespace.

    Raises:
        PhraseError: if *phrase* is not one of the supported forms or
            references a nonexistent date (e.g. "fifth Monday of February"
            in a year where February has no fifth Monday).
    """
    text = phrase.strip().lower()
    if not text:
        raise PhraseError("empty phrase")

    tokens = text.split()
    spec = _parse(tokens)
    if isinstance(spec, _OrdinalWeekdayInMonth):
        d = _ordinal_weekday_in_month(base, spec.ordinal, spec.weekday, spec.month)
    elif isinstance(spec, _LastWeekdayInMonth):
        d = _last_weekday_in_month(base, spec.weekday, spec.month)
    else:  # pragma: no cover - _parse exhausts all forms
        raise PhraseError(f"unrecognised phrase: {phrase!r}")

    return datetime.combine(d, base.timetz())


def _parse(tokens):
    """Dispatch to the correct form or raise PhraseError."""
    if not tokens:
        raise PhraseError("empty token list")

    # last <weekday> of <month>   — 4 tokens
    # last <weekday>               — 2 tokens
    if tokens[0] == "last":
        if len(tokens) == 4 and tokens[2] == "of":
            weekday = _weekday(tokens[1])
            month = _month(tokens[3])
            return _LastWeekdayInMonth(weekday=weekday, month=month)
        if len(tokens) == 2:
            weekday = _weekday(tokens[1])
            return _LastWeekdayInMonth(weekday=weekday, month=None)
        raise PhraseError(f"unrecognised 'last' form: {' '.join(tokens)!r}")

    # <ordinal> <weekday> of <month>  — 4 tokens
    # <ordinal> <weekday>             — 2 tokens
    if tokens[0] in ORDINALS:
        if len(tokens) == 4 and tokens[2] == "of":
            ordinal = ORDINALS[tokens[0]]
            weekday = _weekday(tokens[1])
            month = _month(tokens[3])
            return _OrdinalWeekdayInMonth(ordinal=ordinal, weekday=weekday, month=month)
        if len(tokens) == 2:
            ordinal = ORDINALS[tokens[0]]
            weekday = _weekday(tokens[1])
            return _OrdinalWeekdayInMonth(ordinal=ordinal, weekday=weekday, month=None)
        raise PhraseError(f"unrecognised ordinal form: {' '.join(tokens)!r}")

    raise PhraseError(f"unrecognised phrase: {' '.join(tokens)!r}")


def _weekday(token: str) -> int:
    if token not in WEEKDAYS:
        raise PhraseError(f"unknown weekday: {token!r}")
    return WEEKDAYS[token]


def _month(token: str) -> int:
    if token not in MONTHS:
        raise PhraseError(f"unknown month: {token!r}")
    return MONTHS[token]
