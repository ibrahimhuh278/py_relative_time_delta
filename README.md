# py_relative_time_delta

Applies human relative time phrases like "last Monday of March" or "third Wednesday" to `datetime` objects.

```python
from datetime import datetime, timezone
from py_relative_time_delta import apply_phrase

base = datetime(2024, 3, 13, 10, 30, 0, tzinfo=timezone.utc)

apply_phrase(base, "third Wednesday of March")   # datetime(2024, 3, 20, 10, 30, 0, tzinfo=UTC)
apply_phrase(base, "last Monday")                 # datetime(2024, 3, 25, 10, 30, 0, tzinfo=UTC)
apply_phrase(base, "first Friday of January")     # datetime(2024, 1, 5, 10, 30, 0, tzinfo=UTC)
```

The library exists because `dateutil.relativedelta` is powerful but opaque, and plain `timedelta` can't express "the last Monday of the month." This trades breadth for clarity: four phrase forms only, each mapping to an unambiguous calendar computation. The time component and `tzinfo` of the input datetime are preserved unchanged — only the date is replaced.

Supported forms (case-insensitive):

- `"<ordinal> <Weekday> of <Month>"` — e.g. `"third Wednesday of March"`
- `"<ordinal> <Weekday>"` — uses the month of the input datetime
- `"last <Weekday> of <Month>"` — e.g. `"last Monday of March"`
- `"last <Weekday>"` — uses the month of the input datetime

Ordinals are `first` through `fifth`. The awkward edge: not every month has a fifth occurrence of a given weekday (February often does not). Asking for one raises `PhraseError`, a subclass of `ValueError`. The year is always taken from the input datetime — the library does not jump years.

`apply_phrase(base: datetime, phrase: str) -> datetime` is the only public function. `PhraseError` is raised on any unrecognised or impossible phrase.
