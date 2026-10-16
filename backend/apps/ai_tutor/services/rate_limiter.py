import time
from django.core.cache import cache
from django.conf import settings
from .exceptions import RateLimitExceededError, DailyLimitExceededError


# Default rate limits: 20 requests per minute, 150 requests per day
MINUTE_LIMIT = int(getattr(settings, 'AI_TUTOR_RATE_LIMIT_PER_MINUTE', 20))
DAILY_LIMIT = int(getattr(settings, 'AI_TUTOR_DAILY_LIMIT', 150))


def check_and_record_rate_limit(user_id: int):
    """
    Validates that the user has not exceeded the per-minute or daily
    AI Tutor query limits using cache-backed sliding counters.
    """
    now = int(time.time())

    # 1. Per-minute sliding counter
    minute_key = f"ai_tutor_rate_{user_id}_{now // 60}"
    minute_count = cache.get(minute_key, 0)
    if minute_count >= MINUTE_LIMIT:
        raise RateLimitExceededError(
            f"You have reached the limit of {MINUTE_LIMIT} AI Tutor requests per minute. Please wait a few seconds."
        )

    # 2. Daily counter (24-hour window)
    day_key = f"ai_tutor_daily_{user_id}_{time.strftime('%Y%m%d')}"
    daily_count = cache.get(day_key, 0)
    if daily_count >= DAILY_LIMIT:
        raise DailyLimitExceededError(
            f"You have used your daily allocation of {DAILY_LIMIT} AI Tutor requests. Your quota resets at midnight."
        )

    # Increment counters
    cache.set(minute_key, minute_count + 1, timeout=90)
    cache.set(day_key, daily_count + 1, timeout=86400)


def get_user_usage_stats(user_id: int) -> dict:
    """Returns current rate limit and remaining requests for the user."""
    day_key = f"ai_tutor_daily_{user_id}_{time.strftime('%Y%m%d')}"
    used_today = cache.get(day_key, 0)
    remaining_today = max(0, DAILY_LIMIT - used_today)
    return {
        'used_today': used_today,
        'remaining_today': remaining_today,
        'daily_limit': DAILY_LIMIT,
        'minute_limit': MINUTE_LIMIT
    }
