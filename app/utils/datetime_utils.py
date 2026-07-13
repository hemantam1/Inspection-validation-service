from datetime import datetime

def seconds_between(
    earlier: datetime,
    later: datetime,
) -> float:
    return (later - earlier).total_seconds()


def is_fast_submission(
    seconds: float,
    minimum_interval: int,
) -> bool:
    return seconds < minimum_interval