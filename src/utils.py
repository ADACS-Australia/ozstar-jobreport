import signal
import pyslurm
import traceback
import sys

import numpy as np


def print_stderr(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def get_live_job_data(job_id, debug=False):
    """
    Get live job data from the Slurm controller (scontrol).
    This returns current job state, not historical data from the DB.
    """
    try:
        job = pyslurm.Job.load(job_id)
        return job
    except ValueError:
        if debug:
            print_stderr(f"Warning: job {job_id} not found in Slurm controller")
        return None
    except Exception:
        if debug:
            print_stderr("Warning: could not get live job data from Slurm controller")
            print_stderr(traceback.format_exc())
        return None


def humansize(nbytes, bytes=True):
    """Convert bytes to human readable format"""
    suffixes = ["", "K", "M", "G", "T", "P"]
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0
        i += 1
    f = f"{nbytes:2.1f}".rstrip("0").rstrip(".")
    return f"{f} {suffixes[i]}" + ("B" if bytes else "")


def seconds_to_str(seconds):
    days = seconds // (24 * 60 * 60)
    seconds = seconds % (24 * 60 * 60)
    hours = seconds // (60 * 60)
    seconds = seconds % (60 * 60)
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{days}-{hours:02d}:{minutes:02d}:{seconds:02d}"


def percentage_bar(percentage, width=20, style=None):
    """Return a progress bar for a given percentage"""
    bar = int(min(percentage, 1.0) * width)
    if style == "arrow":
        bar = min(bar, width - 1)
        return f"[{'-' * bar}>{' ' * (width - 1 - bar)}] {percentage:5.1%}"
    else:
        return f"[{'#' * bar}{' ' * (width - bar)}] {percentage:5.1%}"


class Timeout:
    def __init__(self, seconds=1, error_message="Timeout"):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type, value, traceback):
        signal.alarm(0)


def resample(y, n_points):
    """
    Resamples a 1D array to a new number of points using linear interpolation.

    Args:
        y (array-like): The input 1D array of data.
        n_points (int): The desired number of points in the output array.

    Returns:
        np.ndarray: The resampled array.
    """
    y = np.asarray(y)
    assert y.ndim == 1, "Input array must be one-dimensional."

    norig = len(y)
    npoints = int(n_points)

    # Need at least 2 points
    assert norig > 1, "Original array must have more than 1 point."
    assert npoints > 1, "n_points must be greater than 1."

    if npoints != norig:
        # Create the x-coordinates for the original and new arrays
        x_old = np.linspace(0, 1, norig)
        x_new = np.linspace(0, 1, npoints)
        return np.interp(x_new, x_old, y)
    else:
        # If the number of points is the same, return a copy
        return y.copy()


def pretty_time(t):
    """
    Convert timestamps to relative time with appropriate units (sec, mins, hrs, days).

    Args:
        t (array-like): Array of timestamps in seconds

    Returns:
        tuple: (relative_time_array, unit_string)
    """
    minute = 60
    hour = 60*minute
    day = 24*hour
    x = t - t[0]
    tunit = "sec"

    assert x[-1] >= 0

    if x[-1] > 2*day:
        x = x / day
        tunit = "days"
    elif x[-1] > 2*hour:
        x = x / hour
        tunit = "hrs"
    elif x[-1] > 2*minute:
        x = x / minute
        tunit = "mins"

    return x, tunit
