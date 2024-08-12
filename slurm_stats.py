import pyslurm

def get_slurm_stats(job_id):
    """
    Call pyslurm to get stats
    """

    job = get_job(job_id)

    if job["mem_per_cpu"]:
        cpus_per_node = job["num_cpus"] / job["num_nodes"]
        req_mem = job["pn_min_memory"] * cpus_per_node
    else:
        req_mem = job["pn_min_memory"] * job["num_nodes"]

    # Requested memory per node, converted from MB to B
    req_mem = req_mem * 1024**2
    req_nodes = job["num_nodes"]
    elapsed = job["run_time_str"]
    time_limit = job["time_limit_str"]

    data = {
        "req_mem": req_mem,
        "req_nodes": req_nodes,
        "elapsed": elapsed,
        "time_limit": time_limit,
    }

    return data

def get_job(job_id):
    """
    Get the job dict using the array job ID and task ID
    If the unique ID is provided, this will also work
    """
    jobs = pyslurm.job().get()

    # Input job_id is given as ArrayJobId_ArrayTaskId

    # Job is not an array:
    if "_" not in job_id:
        return jobs[int(job_id)]
    else:
        array_id, task_id = job_id.split("_")
        # Find the job with the matching ArrayJobId
        for i in jobs:
            job = jobs[i]
            if job["array_job_id"] == int(array_id) and job["array_task_id"] == int(task_id):
                return job