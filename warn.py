from utils import indentprint


def print_warnings(max_mem, req_mem, avg_cpu):
    """
    Print out any warnings about the job
    """

    count = 0
    warnings = []

    mem_usage_fraction = None
    if max_mem is not None and req_mem is not None:
        mem_usage_fraction = max_mem / req_mem
    if mem_usage_fraction is not None and mem_usage_fraction < 0.5:
        count += 1
        warnings += ["Too much memory requested"]

    if avg_cpu is not None and avg_cpu < 75.0:
        count += 1
        warnings += ["CPU usage is low"]

    if count > 0:
        print("Warnings:")
        indentprint(f"{count} issue{'s' if count > 1 else ''} detected!")
        for w in warnings:
            indentprint(f"- {w}")
