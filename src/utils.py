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

def to_human(x, bytes=True):
    """Convert a number to a human readable format, handling both SI (base 1000) and byte (base 1024) suffixes"""
    if x == 0:
        return 1, ''
    units = ['', 'K', 'M', 'G', 'T', 'P']
    # Note: To be consistent with SLURM, we use e.g. "MB" instead of "MiB"
    if bytes:
        i = int(np.floor(np.log2(x) / 10))
        i = min(i, len(units) - 1)
        fac = 1/ (1024 ** i)
    else:
        i = int(np.floor(np.log10(x) / 3))
        i = min(i, len(units) - 1)
        fac = 1/ (1000 ** i)
    return fac, units[i]

def humansize(nbytes, bytes=True):
    """Convert bytes to human readable format"""

    fac, units = to_human(nbytes, bytes=bytes)

    # Note: To be consistent with SLURM, we use e.g. "MB" instead of "MiB"
    if bytes:
        units += 'B'

    x = f"{nbytes*fac:2.1f}".rstrip("0").rstrip(".")

    return f"{x} {units}"


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


def resample(x, y, n_points):
    """
    Resamples 1D arrays to a new number of points using linear interpolation.

    Args:
        x (array-like): The x-coordinates (e.g., time values).
        y (array-like): The y-coordinates (e.g., data values).
        n_points (int): The desired number of points in the output arrays.

    Returns:
        tuple: (x_resampled, y_resampled) as numpy arrays.
    """
    x = np.asarray(x)
    y = np.asarray(y)

    assert x.ndim == 1, "Input x array must be one-dimensional."
    assert y.ndim == 1, "Input y array must be one-dimensional."
    assert len(x) == len(y), "x and y arrays must have the same length."

    norig = len(y)
    npoints = int(n_points)

    if norig > 1 and npoints > 1:
        # Create new x-coordinates spanning the original range
        x_new = np.linspace(x[0], x[-1], npoints)
        y_new = np.interp(x_new, x, y)
        return x_new, y_new
    else:
        return x.copy(), y.copy()


def human_time(t):
    """
    Scale timestamps (seconds) to the largest reasonable time unit.

    Args:
        t (array-like): timestamps in seconds

    Returns:
        tuple: (scaled_array, unit_string)
    """
    x = np.asarray(t) - t[0]
    maxval = x.max()
    units = ['s', 'min', 'h', 'd']
    scales = [1, 60, 3600, 86400]

    if maxval == 0:
        return x, 's'

    i = np.searchsorted([2*60, 2*3600, 2*86400], maxval, side='right')
    fac = 1 / scales[i]
    return fac, units[i]
