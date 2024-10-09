import pyslurm

from tabulate import tabulate
from utils import humansize, seconds_to_str, percentage_bar


UNFINISHED_STATES = ["PENDING", "RUNNING", "REQUEUED", "RESIZING", "SUSPENDED"]


class JobReport:
    def __init__(self, job_id, influxquery=None):
        self.job_id = job_id
        self.raw_id = self.get_raw_id(str(job_id))
        self.db_data = pyslurm.db.Job.load(self.raw_id)

        if self.db_data.array_id and self.db_data.array_task_id:
            self.influxid = f"{self.db_data.array_id}_{self.db_data.array_task_id}"
        elif "+" in str(self.job_id):
            self.influxid = str(self.raw_id)
        else:
            self.influxid = str(self.job_id)

        self.finished = self.db_data.state not in UNFINISHED_STATES
        self.influxquery = influxquery

        self.report_data = {
            "state": self.db_data.state,
            "req_mem": self.get_req_mem_bytes(),
            "max_mem": self.get_max_mem_bytes(),
            "elapsed_time": self.get_elapsed_time_seconds(),
            "time_limit": self.get_time_limit_seconds(),
            "avg_cpu": self.get_user_cpu_percentage(),
            "avg_gpu": self.get_user_gpu_percentage(),
            "lustre_stats": self.get_lustre_stats(),
        }

        self.warnings = self.get_warnings()
        self.report_data["warnings"] = self.warnings

        self.heading_width = 14

    def __str__(self):
        return self.get_full_report()

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
            return self.influxquery.get_max_mem(self.influxid)
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
            return self.influxquery.get_avg_cpu(self.influxid)
        else:
            return None

    def get_user_gpu_percentage(self):
        """
        Get the user GPU time as a percentage
        (only available via InfluxDB)

        Check if the job is on a GPU partition before attempting to query the InfluxDB server
        """

        if self.influxquery is not None and "gpu" in self.db_data.partition:
            return self.influxquery.get_avg_gpu(self.influxid)
        else:
            return None

    def get_lustre_stats(self):
        """
        Get the Lustre stats for the job
        """

        if self.influxquery is None:
            return None

        data = self.influxquery.get_lustre_jobstats(self.influxid)

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
        max_mem = self.report_data["max_mem"]
        req_mem = self.report_data["req_mem"]
        avg_cpu = self.report_data["avg_cpu"]
        avg_gpu = self.report_data["avg_gpu"]

        mem_usage_fraction = None
        if max_mem is not None and req_mem is not None:
            mem_usage_fraction = max_mem / req_mem
        if mem_usage_fraction is not None and mem_usage_fraction < 0.5:
            warnings += ["Too much memory requested"]

        elapsed_time = self.report_data["elapsed_time"]
        time_limit = self.report_data["time_limit"]

        if avg_cpu is not None and avg_cpu < 75.0:
            if avg_gpu is not None and avg_gpu > 95.0:
                warnings += ["CPU usage is low (possibly GPU-bound)"]
            else:
                warnings += ["CPU usage is low"]

        if avg_gpu is not None and avg_gpu < 75.0:
            if avg_cpu is not None and avg_cpu > 95.0:
                warnings += ["GPU usage is low (possibly CPU-bound)"]
            else:
                warnings += ["GPU usage is low"]

        if self.finished and elapsed_time is not None and time_limit is not None:
            time_usage_fraction = elapsed_time / time_limit
            if time_usage_fraction < 0.7:
                warnings += ["Too much time requested"]

        return warnings

    @staticmethod
    def get_raw_id(job_id):
        """
        Get the raw ID of the job using the array job ID and task ID,
        or the heterogeneous job ID and offset.
        If the raw ID is provided, this does nothing
        """

        raw_id = None

        # Array jobs
        if "_" in job_id:
            array_id, task_id = job_id.split("_")
            # Find all jobs in the array
            db_filter = pyslurm.db.JobFilter(ids=[array_id])
            jobs = pyslurm.db.Jobs.load(db_filter)
            # Find the one with the matching task ID
            for job in jobs.values():
                if job.array_task_id == int(task_id):
                    raw_id = job.id
        # Heterogeneous jobs
        elif "+" in job_id:
            het_job_id, het_job_offset = job_id.split("+")
            raw_id = int(het_job_id) + int(het_job_offset)
        # Standard jobs
        elif job_id.isdigit():
            raw_id = int(job_id)

        if raw_id is None:
            raise KeyError(f"Job ID {job_id} not found")

        return raw_id

    def get_lustre_report(self):
        """
        Construct a report of the Lustre usage
        """

        data = self.report_data["lustre_stats"]

        if data == {} or data is None:
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

        report = f"Lustre Filesystem:\n{lustre_string}"

        return report + "\n"

    def get_mem_report(self):
        """
        Construct a report of the memory usage
        """

        max_mem = self.report_data["max_mem"]
        req_mem = self.report_data["req_mem"]

        # When the job has first started, data is not available
        initialising = self.report_data["elapsed_time"] < 60 and max_mem == 0

        if max_mem is None or req_mem is None or initialising:
            line = "No data available"
        else:
            line = (
                percentage_bar(max_mem / req_mem)
                + f" ({humansize(max_mem)} peak / {humansize(req_mem)})"
            )

        name = "Memory (RAM)"
        return name.ljust(self.heading_width) + line

    def get_cpu_report(self):
        """
        Construct a report of the CPU usage.
        """

        avg_cpu = self.report_data["avg_cpu"]

        # When the job has first started, data is not available
        initialising = self.report_data["elapsed_time"] < 60 and avg_cpu == 0

        if avg_cpu is None or initialising:
            line = "No data available"
        else:
            line = percentage_bar(avg_cpu / 100) + " average"

        name = "CPU"
        return name.ljust(self.heading_width) + line

    def get_gpu_report(self):
        """
        Construct a report of the GPU usage.
        """

        avg_gpu = self.report_data["avg_gpu"]

        if avg_gpu is None:
            return None
        else:
            line = percentage_bar(avg_gpu / 100) + " average"

        name = "GPU"
        return name.ljust(self.heading_width) + line

    def get_time_report(self):
        """
        Construct a report of the time usage
        """

        elapsed_time = self.report_data["elapsed_time"]
        time_limit = self.report_data["time_limit"]

        if elapsed_time is None or time_limit is None:
            line = "No data available"
        else:
            line = (
                percentage_bar(elapsed_time / time_limit, style="arrow")
                + f" ({seconds_to_str(elapsed_time)} / {seconds_to_str(time_limit)})"
            )

        name = "Time"
        return name.ljust(self.heading_width) + line

    def get_warnings_report(self):
        """
        Construct a report of the warnings
        """

        warnings = self.report_data["warnings"]

        # Don't show warnings when the job has just started
        initialising = self.report_data["elapsed_time"] < 60

        if warnings is None or len(warnings) == 0 or initialising:
            report = ""
        else:
            header = ["Warnings:"]
            report = "\n".join(header + [f"  - {w}" for w in warnings])

        return report + "\n"

    def get_full_report(self):
        """
        Construct a full report of the job
        """

        report_list = [
            self.get_mem_report(),
            self.get_cpu_report(),
            self.get_gpu_report(),
            self.get_time_report(),
            "",
            self.get_lustre_report(),
            self.get_warnings_report(),
        ]

        # Any Nones in the list are for disabled values - remove them
        report_list = [line for line in report_list if line is not None]

        report = "\n".join(report_list)

        # Remove the last newline
        report = report.strip("\n")

        lines = report.split("\n")

        # add a title
        title = f"Job Report: {self.job_id} ({self.report_data['state']})"

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

        report = "\n".join(
            [title_line]
            + [f"| {line.ljust(max_len)} |" for line in lines]
            + [bottom_border]
        )

        return report
