from utils import indentprint


def time_to_seconds(time_string):
    if "-" in time_string:
        days, time = time_string.split("-")
    else:
        days = 0
        time = time_string
    hours, minutes, seconds = time.split(":")
    return (
        int(days) * 24 * 60 * 60
        + int(hours) * 60 * 60
        + int(minutes) * 60
        + int(seconds)
    )

def seconds_to_str(seconds):
    days = seconds // (24 * 60 * 60)
    seconds = seconds % (24 * 60 * 60)
    hours = seconds // (60 * 60)
    seconds = seconds % (60 * 60)
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{days}-{hours:02d}:{minutes:02d}:{seconds:02d}"


def print_time_summary(data):
    """
    Print a summary of the elapsed and requested time
    """

    limit = data["time_limit"]
    elapsed = data["elapsed"]
    state = data["state"]

    # Fraction of time used
    frac = elapsed / limit

    print("Time:")
    indentprint(f"Requested: {seconds_to_str(limit)}")
    indentprint(f"Elapsed:   {seconds_to_str(elapsed)} ({100*frac:.1f}%)")
    indentprint(f"State:     {state}")
