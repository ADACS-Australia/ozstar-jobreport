try:
    from .job_load import load
except ModuleNotFoundError as e:
    import sys
    print("\nError: have you compiled the 'jobload' Cython extension?", file=sys.stderr)
    raise e


__all__ = ["load"]
