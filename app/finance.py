from datetime import date, datetime, time, timedelta, timezone
from decimal import Context, Decimal, localcontext
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


DEFAULT_TIMEZONE = "Asia/Kolkata"
UTC = timezone.utc
ZERO = Decimal("0.00")
CENT = Decimal("0.01")
MONEY_CONTEXT = Context(prec=80)


def money(value) -> Decimal:
    """Return exact two-decimal money without the default Decimal precision limit."""
    with localcontext(MONEY_CONTEXT):
        return Decimal(str(value if value is not None else 0)).quantize(CENT)


def money_sum(values) -> Decimal:
    with localcontext(MONEY_CONTEXT):
        return sum((money(value) for value in values), ZERO).quantize(CENT)


def money_difference(left, right) -> Decimal:
    with localcontext(MONEY_CONTEXT):
        return (money(left) - money(right)).quantize(CENT)


def user_zone(timezone_name: str | None) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name or DEFAULT_TIMEZONE)
    except ZoneInfoNotFoundError:
        return ZoneInfo(DEFAULT_TIMEZONE)


def to_utc(value: datetime, zone: ZoneInfo) -> datetime:
    local_value = value if value.tzinfo else value.replace(tzinfo=zone)
    return local_value.astimezone(UTC)


def in_user_timezone(value: datetime, zone: ZoneInfo) -> datetime:
    utc_value = value if value.tzinfo else value.replace(tzinfo=UTC)
    return utc_value.astimezone(zone)


def utc_day_bounds(
    start_date: date | None,
    end_date: date | None,
    zone: ZoneInfo,
) -> tuple[datetime | None, datetime | None]:
    start = (
        to_utc(datetime.combine(start_date, time.min), zone)
        if start_date is not None
        else None
    )
    end = (
        to_utc(datetime.combine(end_date + timedelta(days=1), time.min), zone)
        if end_date is not None
        else None
    )
    return start, end


def month_bounds(year: int, month: int, zone: ZoneInfo) -> tuple[datetime, datetime]:
    start_date = date(year, month, 1)
    next_month = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    start, end = utc_day_bounds(start_date, next_month - timedelta(days=1), zone)
    return start, end


def month_key(value: datetime, zone: ZoneInfo) -> tuple[int, int]:
    local_value = in_user_timezone(value, zone)
    return local_value.year, local_value.month


def is_complete_budget_month(
    year: int,
    month: int,
    start_date: date | None,
    end_date: date | None,
) -> bool:
    month_start = date(year, month, 1)
    next_month = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    month_end = next_month - timedelta(days=1)
    return (
        (start_date is None or start_date <= month_start)
        and (end_date is None or end_date >= month_end)
    )


def range_contains_complete_month(start_date: date | None, end_date: date | None) -> bool:
    if start_date is None or end_date is None:
        return True

    first_month = date(start_date.year, start_date.month, 1)
    if start_date > first_month:
        first_month = (
            date(start_date.year + 1, 1, 1)
            if start_date.month == 12
            else date(start_date.year, start_date.month + 1, 1)
        )

    last_month = date(end_date.year, end_date.month, 1)
    next_month = (
        date(end_date.year + 1, 1, 1)
        if end_date.month == 12
        else date(end_date.year, end_date.month + 1, 1)
    )
    if end_date < next_month - timedelta(days=1):
        last_month = (
            date(end_date.year - 1, 12, 1)
            if end_date.month == 1
            else date(end_date.year, end_date.month - 1, 1)
        )
    return first_month <= last_month
