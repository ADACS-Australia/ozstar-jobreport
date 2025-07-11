import signal
import pyslurm
import traceback
import sys


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
