from influx import query
from utils import humansize, indentprint

SEARCH_WINDOW = "7d"


def get_max_mem(job_id, pyslurm_data):
    """
    Query Influx for slurm memory stats
    """

    # To reduce load on InfluxDB server, only query it for actively running jobs
    # Otherwise, use the max memory from the Slurm DB (which is only available after job completion)
    if pyslurm_data["state"] != "RUNNING":
        return pyslurm_data["max_mem"]

    # Query for the max memory usage of any node in the job
    job_query = f"""
    from(bucket: "jobmon-stats")
    |> range(start: -{SEARCH_WINDOW})
    |> filter(fn: (r) => r["_measurement"] == "job_max_memory")
    |> filter(fn: (r) => r["job_id"] == "{job_id}")
    |> last()
    """

    job_results = query(job_query)

    if len(job_results) > 0:
        # Get the max value and convert MB to B
        return job_results[0].records[0].get_value() * 1024 ** 2
    else:
        return None


def print_mem_summary(max_mem, requested_mem):
    """
    Print a summary of the memory usage
    """
    print("Memory (RAM):")
    indentprint(f"Requested: {humansize(requested_mem)}")
    if max_mem is None:
        indentprint("No memory usage data available")
    else:
        indentprint(
            f"Peak:      {humansize(max_mem)} ({100*max_mem/requested_mem:.1f}%)"
        )
