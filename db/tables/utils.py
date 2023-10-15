import datetime as dt


def get_utc_timestamp_now() -> float:
    """
    Get current time UTC-0 as timestamp
    """

    return dt.datetime.utcnow().timestamp()
