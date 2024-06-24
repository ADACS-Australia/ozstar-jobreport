from influx import query
from utils import indentprint

SEARCH_WINDOW = "7d"


def get_avg_cpu(job_id):
    """
    Query Influx for CPU usage and calculate the average
    """

    job_query = f"""
    from(bucket: "jobmon-stats")
    |> range(start: -{SEARCH_WINDOW})
    |> filter(fn: (r) => r["_measurement"] == "average_cpu_usage")
    |> filter(fn: (r) => r["job_id"] == "{job_id}")
    |> mean()
    """

    job_results = query(job_query)

    if len(job_results) > 0:
        return job_results[0].records[0].get_value()
    else:
        return None


def print_cpu_summary(avg_usage):
    print("CPU:")
    if avg_usage is None:
        indentprint("No CPU usage data available")
    else:
        indentprint(f"Average CPU Usage: {avg_usage:.1f}%")
