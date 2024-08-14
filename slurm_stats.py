import pyslurm

def get_slurm_stats(job_id):
    """
    Call pyslurm to get stats
    """

    unique_id = get_unique_id(job_id)
    db = get_db_data(unique_id)

    data = {
        "state": db.state,
        "req_mem": req_mem_bytes(db),
        "max_mem": max_mem_bytes(db),
        "elapsed": elapsed_time_seconds(db),
        "time_limit": time_limit_seconds(db),
        "avg_cpu": get_user_cpu_time(db),
    }

    return data

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

def get_submit_data(unique_id):
    """
    Get the job submit dict using the unique ID
    """
    jobs = pyslurm.job().get()
    return jobs[unique_id]

def get_db_data(unique_id):
    """
    Get the job data from the database using the unique ID
    """
    return pyslurm.db.Job.load(unique_id)

def req_mem_bytes(db):
    """
    Get the requested memory per node in bytes from the DB
    """

    # Num nodes will be 0 if job has not started
    if db.num_nodes == 0:
        return 0

    return (db.memory / db.num_nodes) * 1024**2 # convert MB to B

def max_mem_bytes(db):
    """
    Get the max memory usage of any node in the job in bytes
    """
    return db.stats.max_resident_memory

def elapsed_time_seconds(db):
    """
    Get the elapsed time in seconds
    """
    if db.elapsed_time is not None:
        return db.elapsed_time
    else:
        return 0

def time_limit_seconds(db):
    """
    Get the time limit in seconds
    """
    return db.time_limit*60 # convert minutes to seconds

def get_user_cpu_time(db):
    """
    Get the user CPU time as a percentage
    """

    if db.stats.elapsed_cpu_time == 0:
        return 0

    user_cpu = 0
    for step in db.steps.values():
        user_cpu += step.stats.user_cpu_time

    return user_cpu / db.stats.elapsed_cpu_time * 100

def is_running(job_id=None, db=None):
    """
    Check if the job is running
    """
    try:
        if db is None:
            if job_id is None:
                raise ValueError("Either job_id or db must be provided")
            unique_id = get_unique_id(job_id)
            db = get_db_data(unique_id)

        if db.state == "RUNNING":
            return True
    except KeyError:
        return False

    return False

def get_stdout_file(job_id):
    """
    Get the path to the stdout file for the job
    """
    unique_id = get_unique_id(job_id)
    db = get_db_data(unique_id)

    if is_running(db=db):
        submit = get_submit_data(unique_id)
        return submit["std_out"]
    else:
        print("Job is not running, could not get stdout file")

    return None
