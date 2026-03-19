from datetime import datetime, timedelta, timezone


def calculate_next_review(quality: int, ease_factor: float, interval: int) -> dict:
    """
    Implements the SM-2 Spaced Repetition algorithm.

    Args:
        quality: Recall quality score 0-5.
                 0 = complete blackout, 5 = perfect recall.
        ease_factor: Current ease factor (e-factor). Min 1.3.
        interval: Current interval in days.

    Returns:
        A dict with new 'interval', 'ease_factor', and 'next_review_date'.
    """
    if quality < 0 or quality > 5:
        raise ValueError("quality must be between 0 and 5")

    # --- Calculate new interval ---
    if quality >= 3:
        if interval == 0:
            new_interval = 1
        elif interval == 1:
            new_interval = 6
        else:
            new_interval = round(interval * ease_factor)
    else:
        # Failed recall: reset to beginning
        new_interval = 1

    # --- Update ease factor ---
    # Formula: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

    # Ease factor must never drop below 1.3
    new_ef = max(1.3, round(new_ef, 4))

    # --- Compute next review date (UTC-aware) ---
    next_review_date = datetime.now(timezone.utc) + timedelta(days=new_interval)

    return {
        "interval": new_interval,
        "ease_factor": new_ef,
        "next_review_date": next_review_date,
    }
