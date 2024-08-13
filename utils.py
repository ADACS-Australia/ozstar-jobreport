import subprocess
import signal
import sys

suffixes = ["", "K", "M", "G", "T", "P"]


def humansize(nbytes, bytes=True):
    """Convert bytes to human readable format"""
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0
        i += 1
    f = f"{nbytes:2.1f}".rstrip("0").rstrip(".")
    return f"{f} {suffixes[i]}" + ("B" if bytes else "")


def bytesize(human):
    """Convert human readable format to bytes"""

    # Remove bytes suffix if present
    human = human.replace("B", "")

    suffix = human[-1]
    if suffix not in suffixes:
        raise ValueError(f"Invalid suffix: {suffix}")
    power = suffixes.index(suffix)
    return float(human[:-1]) * 1024 ** power


def cmd(command):
    """Run a command and return the output"""
    return subprocess.check_output(command, shell=True).decode("utf-8").strip()


def indentprint(text, indent=1):
    """Print multiline text with indentation"""
    spaces = "  " * indent
    print(spaces + text.replace("\n", "\n" + spaces))


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

def redirect_stdout_to_file(file):
    """
    Redirect stdout to a file
    """
    # Check for write permissions to the file
    try:
        with open(file, "a") as f:
            pass
    except PermissionError:
        print(f"Permission denied to write to {file}")
        return

    print(f"Appending to file: {file}")
    sys.stdout = open(file, "a")
