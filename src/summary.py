import traceback
import pyslurm

from tabulate import tabulate
from utils import humansize, seconds_to_str, percentage_bar


UNFINISHED_STATES = ["PENDING", "RUNNING", "REQUEUED", "RESIZING", "SUSPENDED"]


class JobSummary:
    def __init__(self, job_id, influxquery=None):
        self.job_id = self.get_unique_id(str(job_id))
        self.db_data = pyslurm.db.Job.load(self.job_id)
        self.finished = self.db_data.state not in UNFINISHED_STATES
        self.influxquery = influxquery

        self.summary_data = {
            "state": self.db_data.state,
            "req_mem": self.get_req_mem_bytes(),
            "max_mem": self.get_max_mem_bytes(),
            "elapsed_time": self.get_elapsed_time_seconds(),
            "time_limit": self.get_time_limit_seconds(),
            "avg_cpu": self.get_user_cpu_percentage(),
            "lustre_stats": self.get_lustre_stats(),
        }

        self.warnings = self.get_warnings()
        self.summary_data["warnings"] = self.warnings

        self.heading_width = 14

    def __str__(self):
        return self.get_full_summary()

    def get_req_mem_bytes(self):
        """
        Get the requested memory per node in bytes from the DB
        """

        # Num nodes will be 0 if job has not started
        if self.db_data.num_nodes == 0:
            return 0
        else:
            return (
                self.db_data.memory / self.db_data.num_nodes
            ) * 1024**2  # convert MB to B

    def get_max_mem_bytes(self):
        """
        Get the max memory usage of any node in the job in bytes
        """

        if self.finished:
            return self.db_data.stats.max_resident_memory
        elif self.influxquery is not None:
            return self.influxquery.get_max_mem(self.job_id)
        else:
            return None

    def get_elapsed_time_seconds(self):
        """
        Get the elapsed time in seconds
        """

        if self.db_data.elapsed_time is not None:
            return self.db_data.elapsed_time
        else:
            return 0

    def get_time_limit_seconds(self):
        """
        Get the time limit in seconds
        """
        return self.db_data.time_limit * 60  # convert minutes to seconds

    def get_user_cpu_percentage(self):
        """
        Get the user CPU time as a percentage
        """

        if self.finished:
            if self.db_data.stats.elapsed_cpu_time == 0:
                return 0

            user_cpu = 0
            for step in self.db_data.steps.values():
                user_cpu += step.stats.user_cpu_time

            return user_cpu / self.db_data.stats.elapsed_cpu_time * 100

        elif self.influxquery is not None:
            return self.influxquery.get_avg_cpu(self.job_id)
        else:
            return None

    def get_lustre_stats(self):
        """
        Get the Lustre stats for the job
        """

        if self.influxquery is None:
            return None

        data = self.influxquery.get_lustre_jobstats(self.job_id)

        def get_last_value(fs, server, field):
            """Get the last value, but if data is not available, return 0"""
            try:
                value = data[fs][server][field]["value"][-1]
            except KeyError:
                value = 0
            return value

        lustre_stats = {}

        for fs in list(data.keys()):
            lustre_stats[fs] = {}

            lustre_stats[fs]["total_read"] = get_last_value(fs, "oss", "read_bytes")
            lustre_stats[fs]["total_write"] = get_last_value(fs, "oss", "write_bytes")
            lustre_stats[fs]["total_iops"] = get_last_value(fs, "mds", "iops")

        return lustre_stats

    def get_warnings(self):
        """
        Construct a list of warnings for the job
        """
        warnings = []
        max_mem = self.summary_data["max_mem"]
        req_mem = self.summary_data["req_mem"]
        avg_cpu = self.summary_data["avg_cpu"]

        mem_usage_fraction = None
        if max_mem is not None and req_mem is not None:
            mem_usage_fraction = max_mem / req_mem
        if mem_usage_fraction is not None and mem_usage_fraction < 0.5:
            warnings += ["Too much memory requested"]

        if avg_cpu is not None and avg_cpu < 75.0:
            warnings += ["CPU usage is low"]

        return warnings

    @staticmethod
    def get_unique_id(job_id):
        """
        Get the unique ID of the job using the array job ID and task ID
        If the unique ID is provided, this does nothing
        """

        if "_" not in job_id and job_id.isdigit():
            return int(job_id)

        # Convert the array ID to the unique job ID
        array_id, task_id = job_id.split("_")

        db_filter = pyslurm.db.JobFilter(ids=[str(array_id)])
        jobs = pyslurm.db.Jobs.load(db_filter)

        unique_id = None
        for job in jobs.values():
            if job.array_task_id == int(task_id):
                unique_id = job.id

        if unique_id is None:
            raise KeyError(f"Job ID {job_id} not found")

        return unique_id

    def get_stdout_file(self, debug=False):
        """
        Get the path to the stdout file for the job
        """

        stdout_file = None

        if self.db_data.state == "PENDING":
            print("Warning: could not get stdout file -- job has not started ")
        else:
            try:
                job = pyslurm.job().find_id(self.job_id)
                stdout_file = job[0]["std_out"]
            except ValueError:
                print(
                    "Warning: could not get stdout file -- job may have finished too long ago"
                )
                if debug:
                    print(traceback.format_exc())

        return stdout_file

    def get_lustre_summary(self):
        """
        Construct a summary of the Lustre usage
        """

        data = self.summary_data["lustre_stats"]

        if data is None:
            lustre_string = "  No data available"
        else:
            fs_names = {
                "dagg": "/fred",
                "home": "/home",
                "apps": "/apps",
                "images": "OS",
            }
            table = []
            for fs in data:
                table += [
                    [
                        fs_names[fs],
                        humansize(data[fs]["total_read"]),
                        humansize(data[fs]["total_write"]),
                        humansize(data[fs]["total_iops"], bytes=False),
                    ]
                ]

            table = tabulate(
                table,
                headers=["Path", "Total Read", "Total Write", "Total IOPS"],
            )
            indent = 2 * " "
            lustre_string = indent + table.replace("\n", "\n" + indent)

        summary = f"Lustre Filesystem:\n{lustre_string}"

        return summary + "\n"

    def get_mem_summary(self):
        """
        Construct a summary of the memory usage
        """

        max_mem = self.summary_data["max_mem"]
        req_mem = self.summary_data["req_mem"]

        if max_mem is None or req_mem is None:
            line = "No data available"
        else:
            line = (
                percentage_bar(max_mem / req_mem)
                + f" ({humansize(max_mem)} peak / {humansize(req_mem)})"
            )

        name = "Memory (RAM)"
        return name.ljust(self.heading_width) + line

    def get_cpu_summary(self):
        """
        Construct a summary of the CPU usage.
        """

        avg_cpu = self.summary_data["avg_cpu"]

        if avg_cpu is None:
            line = "No data available"
        else:
            line = percentage_bar(avg_cpu / 100) + " average"

        name = "CPU"
        return name.ljust(self.heading_width) + line

    def get_time_summary(self):
        """
        Construct a summary of the time usage
        """

        elapsed_time = self.summary_data["elapsed_time"]
        time_limit = self.summary_data["time_limit"]

        if elapsed_time is None or time_limit is None:
            line = "No data available"
        else:
            line = (
                percentage_bar(elapsed_time / time_limit, style="arrow")
                + f" ({seconds_to_str(elapsed_time)} / {seconds_to_str(time_limit)})"
            )

        name = "Time"
        return name.ljust(self.heading_width) + line

    def get_warnings_summary(self):
        """
        Construct a summary of the warnings
        """

        warnings = self.summary_data["warnings"]

        if warnings is None or len(warnings) == 0:
            summary = ""
        else:
            header = ["Warnings:"]
            summary = "\n".join(header + [f"  - {w}" for w in warnings])

        return summary + "\n"

    def get_full_summary(self):
        """
        Construct a full summary of the job
        """

        summary_list = [
            self.get_mem_summary(),
            self.get_cpu_summary(),
            self.get_time_summary(),
            "",
            self.get_lustre_summary(),
            self.get_warnings_summary(),
        ]

        summary = "\n".join(summary_list)

        # Remove the last newline
        summary = summary.strip("\n")

        lines = summary.split("\n")

        # add a title
        title = f"Job Summary: {self.job_id} ({self.summary_data['state']})"

        # find longest line
        max_len = max(max([len(line) for line in lines]), len(title))

        # top border line with embedded title
        ndash = max_len - len(title)
        ldashes = "-" * (ndash // 2)
        rdashes = "-" * (ndash // 2)
        if ndash % 2 == 1:
            rdashes += "-"
        title_line = "+" + ldashes + " " + title + " " + rdashes + "+"

        # bottom border
        bottom_border = "+" + "-" * (max_len + 2) + "+"

        summary = "\n".join(
            [title_line]
            + [f"| {line.ljust(max_len)} |" for line in lines]
            + [bottom_border]
        )

        return summary
