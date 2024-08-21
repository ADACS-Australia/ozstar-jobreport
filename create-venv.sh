#!/bin/bash -e

if [ -z "$SLURM_INCLUDE_DIR" ]; then
    echo "Warning: SLURM_INCLUDE_DIR not set. PySlurm will use: /usr/include/"
fi
if [ -z "$SLURM_LIB_DIR" ]; then
    echo "Warning: SLURM_LIB_DIR not set. PySlurm will use: /usr/lib64/"
fi

echo "==> Creating venv..."
python3 -m venv venv/jobsummary

echo "==> Activating venv..."
source venv/bin/activate

echo "==> Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt
