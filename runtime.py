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


def print_time_summary(sacct_data):
    """
    Print a summary of the elapsed and requested time
    """

    limit_string = sacct_data["time_limit"]
    elapsed_string = sacct_data["elapsed"]

    # If the limit has days ("-" in the string) then ensure that the elapsed
    # time has days or has padded spaces
    if "-" in limit_string:
        if "-" in elapsed_string:
            elapsed_string = elapsed_string.rjust(len(limit_string))
        else:
            elapsed_string = elapsed_string.rjust(len(limit_string), " ")

    # Fraction of time used
    frac = time_to_seconds(elapsed_string) / time_to_seconds(limit_string)

    print("Time:")
    indentprint(f"Requested: {limit_string}")
    indentprint(f"Elapsed:   {elapsed_string} ({100*frac:.1f}%)")
