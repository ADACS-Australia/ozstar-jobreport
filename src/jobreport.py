import sys
import argparse
import traceback

from socket import gethostname
from pathlib import Path
from utils import Timeout, get_live_job_data, print_stderr
from stdout_expansion import expand_stdout
from report import JobReport
from influx import InfluxQuery


def get_report(job_id, influx_config=None, debug=False, plot=False):
    query = None

    # Initialize InfluxQuery if the configuration file exists
    if influx_config is not None and Path(influx_config).exists():
        try:
            query = InfluxQuery(Path(influx_config), retries=3, verbose=debug)
        except Exception:
            print_stderr("Warning: InfluxQuery could not be initialized")
            if debug:
                print_stderr(traceback.format_exc())
    else:
        print_stderr("Warning: InfluxDB configuration file not found")

    job_report = JobReport(job_id, query, plot)
    return job_report


def main(job_id, epilog=False, influx_config=None, debug=False, plot=False):
    raw_id = JobReport.get_raw_id(job_id)
    stdout_file = None
    batch_host = None
    is_batch_job = True

    # Get live job data from Slurm controller (not DB)
    job_data = get_live_job_data(raw_id, debug)

    if job_data is not None:
        if job_data.standard_output is not None:
            stdout_file = expand_stdout(job_data)
            stdout_file = Path(stdout_file)
        batch_host = job_data.batch_host
        is_batch_job = bool(job_data.is_batch_job)

    # Ensure that this only runs on the batch host if in epilog mode
    if epilog and batch_host != gethostname():
        if debug:
            print_stderr(
                "Warning: job report in epilog mode can only be run on the batch host"
            )
        return

    if epilog and not is_batch_job:
        if debug:
            print_stderr(
                "Warning: job report in epilog mode can only be run for batch jobs"
            )
        return

    # Create job report
    job_report = get_report(job_id, influx_config, debug, plot)

    # Do nothing if in epilog mode and the job hasn't finished
    if epilog and not job_report.finished:
        print_stderr("Warning: job has not finished yet")
        return

    # Print/write the report
    if job_report is not None:
        if epilog and stdout_file is not None and job_report.finished:
            if stdout_file.exists():
                try:
                    with open(stdout_file, "a") as file:
                        print_stderr(
                            f"Appending jobid {job_report.raw_id} report to: {stdout_file}"
                        )
                        file.write("\n" + str(job_report) + "\n")
                except PermissionError:
                    print_stderr("Error: permission denied writing to job stdout file")
            else:
                raise FileNotFoundError(
                    f"Error: job stdout file {stdout_file} not found"
                )
        else:
            print(job_report)


if __name__ == "__main__":
    # Get command line args
    parser = argparse.ArgumentParser(
        description="Print out a report of the job", prog="jobreport"
    )
    parser.add_argument("job_id", type=str, help="Job ID")
    parser.add_argument(
        "-e",
        "--epilog",
        action="store_true",
        help="Append to the job's stdout file in Slurm epilog",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Allow debug output (e.g. stack traces) to be printed",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds for the job report",
    )
    parser.add_argument(
        "-c",
        "--influx-config",
        type=str,
        help="InfluxDB configuration file",
    )
    parser.add_argument(
        "-p",
        "--plot",
        "--plot-width",
        nargs="?",
        type=int,
        const=True,
        default=False,
        help="Generate plots for the job report (optionally specify a plot width)",
    )

    args = parser.parse_args()

    # for nicer output in slurmd logs
    if args.epilog:
        print_stderr("")

    # Handle exceptions at the top level
    try:
        # Ensure the code does not hang
        with Timeout(int(args.timeout)):
            main(args.job_id, args.epilog, args.influx_config, args.debug, args.plot)

    # Print exception tracebacks if in debug mode
    except Exception:
        print_stderr("Error: job report could not be generated")
        if args.debug:
            raise
        sys.exit(1)
