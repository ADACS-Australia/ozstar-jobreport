import os
import sys
import pyslurm
from pathlib import Path
from setuptools import Extension, setup
from Cython.Build import cythonize

try:
    from packaging.version import Version
except ImportError:
    from setuptools._vendor.packaging.version import Version


def build_package():

    slurm_lib_dir = Path(os.getenv("SLURM_LIB_DIR", "/usr/lib64"))
    slurm_inc_dir = Path(os.getenv("SLURM_INCLUDE_DIR", "/usr/include"))

    # Check slurm version matches pyslurm
    slurm_version = None
    slurm_version_h = slurm_inc_dir / "slurm" / "slurm_version.h"
    if not slurm_version_h.exists():
        raise RuntimeError(f"Cannot locate slurm_version.h in {slurm_inc_dir}")

    with open(slurm_version_h, "r", encoding="latin-1") as f:
        for line in f:
            if line.find("#define SLURM_VERSION_NUMBER") == 0:
                _slurm_version = line.split(" ")[2].strip()
                vers = int(_slurm_version, 16)
                major = vers >> 16 & 0xFF
                minor = vers >> 8 & 0xFF
                slurm_version = f"{major}.{minor}"
                print("Detected Slurm version - " f"{slurm_version}")

    if slurm_version is None:
        raise RuntimeError("Unable to detect Slurm version")

    pyslurm_version = pyslurm.__version__
    print(f"Detected PySlurm version - {pyslurm_version}")
    slurm_v = Version(slurm_version)
    pyslurm_v = Version(pyslurm_version)
    if (slurm_v.major, slurm_v.minor) != (pyslurm_v.major, pyslurm_v.minor):
        raise RuntimeError(
            "Slurm and PySlurm version mismatch: "
            f"requires Slurm {pyslurm_version} (major.minor), found {slurm_version}"
        )
    else:
        print("OK")

    pyslurm_dir = os.path.dirname(os.path.dirname(pyslurm.__file__))

    ext = Extension(
        name="job_load",
        sources=["src/jobload.pyx"],
        include_dirs= [str(slurm_inc_dir), str(pyslurm_dir)],
        library_dirs= [str(slurm_lib_dir)],
        libraries= ["slurm"],
        runtime_library_dirs= [str(slurm_lib_dir)],
    )

    saved_args = sys.argv

    # Simulate: python setup.py build_ext
    sys.argv = [sys.argv[0], "build_ext"]

    setup(
        name="job_load",
        python_requires=">=3.6",
        ext_modules=cythonize(ext, nthreads=1, language_level="3"),
        options={
            "build_ext": {
                "inplace": True,
            }
        },
    )

    sys.argv = saved_args

if __name__ == "__main__":
    build_package()
