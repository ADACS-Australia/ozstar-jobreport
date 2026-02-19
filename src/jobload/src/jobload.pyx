from pyslurm import RPCError
from pyslurm.core.error import verify_rpc

# Import the C-level declarations
from pyslurm.core.job.job cimport Job
cimport pyslurm.slurm as slurm
from pyslurm.slurm cimport (
    job_info_msg_t,
    slurm_load_job,
    slurm_free_job_info_msg,
    slurm_init,
)


def load(job_id):
    """
    Implenentation of `pyslurm.job.load` that avoids loading job steps, to avoid a PySlurm bug.
    """

    cdef:
        job_info_msg_t *info = NULL
        Job wrap = None

    # Initialize Slurm before any API calls
    slurm_init(NULL)

    try:
        verify_rpc(slurm_load_job(&info, job_id, slurm.SHOW_DETAIL))

        if info and info.record_count:
            wrap = Job.from_ptr(&info.job_array[0])
            info.record_count = 0

        else:
            raise RPCError(msg=f"RPC was successful but got no job data, "
                            "this should never happen")
    except Exception as e:
        raise e
    finally:
        slurm_free_job_info_msg(info)

    return wrap
