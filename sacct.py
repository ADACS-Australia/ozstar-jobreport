from utils import cmd

SACCT = "/apps/slurm/latest/bin/sacct"
FORMAT = "--format=ReqMem,ReqNodes,Elapsed,TimeLimit"


def call_sacct(job_id):
    """
    Call sacct to get stats
    """
    output = cmd(f"{SACCT} -j {job_id} {FORMAT} --noheader")
    req_mem, req_nodes, elapsed, time_limit = output.split()[0:4]

    data = {
        "req_mem": req_mem,
        "req_nodes": req_nodes,
        "elapsed": elapsed,
        "time_limit": time_limit,
    }

    return data
