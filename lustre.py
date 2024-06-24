from influx import query
from utils import humansize, indentprint
from tabulate import tabulate

SEARCH_WINDOW = "7d"


def get_lustre_jobstats(job_id):
    """
    Query Influx for the Lustre jobstats
    """

    job_query = f"""
    from(bucket: "lustre-jobstats")
    |> range(start: -{SEARCH_WINDOW})
    |> filter(fn: (r) => r["_measurement"] == "lustre")
    |> filter(fn: (r) => r["job"] == "{job_id}")
    |> last()
    """

    job_results = query(job_query)

    data = {}

    for table in job_results:

        fs = table.records[0]["fs"]
        server = table.records[0]["server"]
        field = table.records[0].get_field()

        if fs not in data:
            data[fs] = {}
        if server not in data[fs]:
            data[fs][server] = {}
        if field not in data[fs][server]:
            data[fs][server][field] = {"ts": [], "value": []}

        for record in table:
            ts = int(record.get_time().timestamp())
            data[fs][server][field]["ts"] += [ts]
            data[fs][server][field]["value"] += [record.get_value()]

    return data


def get_summary(job_id):
    """Get a summary of the job (final values)"""
    data = get_lustre_jobstats(job_id)

    def get_last_value(fs, server, field):
        """Get the last value, but if data is not available, return 0"""
        try:
            value = data[fs][server][field]["value"][-1]
        except KeyError:
            value = 0
        return value

    summary = {}

    for fs in list(data.keys()):
        summary[fs] = {}

        summary[fs]["total_read"] = get_last_value(fs, "oss", "read_bytes")
        summary[fs]["total_write"] = get_last_value(fs, "oss", "write_bytes")
        summary[fs]["total_iops"] = get_last_value(fs, "mds", "iops")

    return summary


def print_lustre_summary(summary):
    """Print out a summary as a table"""

    fs_names = {"dagg": "/fred", "home": "/home", "apps": "/apps", "images": "OS"}

    table = []
    for fs in summary:
        table += [
            [
                fs_names[fs],
                humansize(summary[fs]["total_read"]),
                humansize(summary[fs]["total_write"]),
                humansize(summary[fs]["total_iops"], bytes=False),
            ]
        ]

    print("Lustre Filesystem:")
    indentprint(
        tabulate(table, headers=["Path", "Total Read", "Total Write", "Total I/O Operations"])
    )
