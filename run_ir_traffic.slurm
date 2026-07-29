#!/bin/bash
#SBATCH --job-name=ir-traffic-daily
#SBATCH --partition=shared
#SBATCH --account=sdp178
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=4000
#SBATCH --time=00:30:00
#SBATCH --array=0-23%4
#SBATCH --output="joblogs/slurm-%A_%a.out"
#SBATCH --mail-user=YOUR_EMAIL_HERE
#SBATCH --mail-type=BEGIN,END

# One array task per day, 2026-02-10 (task 0) through 2026-03-05 (task 23).
# %4 keeps at most 4 tasks running at once so this doesn't hog the shared partition.
START_DATE="2026-02-10"
CURRENT_DATE=$(date -u -d "${START_DATE} + ${SLURM_ARRAY_TASK_ID} days" +%Y-%m-%d)

REPO_DIR=/home/${USER}/nids-ucsdnt-expanse
PROJ_DIR=/expanse/lustre/projects/${ETP26_ACCOUNT}
USERPROJ_DIR=${PROJ_DIR}/${USER}

# Shared across all array tasks (SLURM_ARRAY_JOB_ID is constant for the whole array;
# SLURM_JOB_ID differs per task) so every day's Parquet files land in one place.
OUTPUT_DIR=${USERPROJ_DIR}/output/ir_traffic/${SLURM_ARRAY_JOB_ID}

mkdir -p ${OUTPUT_DIR}
mkdir -p joblogs

module load singularitypro

# Same container used for the ft-demo.py batch example in 3_running_batch_job.
# Build/locate your own .sif per that folder's README and point BATCH_SIF at it.
BATCH_SIF=${USERPROJ_DIR}/etppybatch.sif

# Spark driver memory should stay comfortably below --cpus-per-task * --mem-per-cpu
# (4 * 4000MB = ~16g here), leaving headroom for the container/OS - see ir_traffic_batch.py.
singularity exec --env-file ${USERPROJ_DIR}/.ucsdnts3.env \
    --bind ${OUTPUT_DIR}:/output,${REPO_DIR}:/etp,/tmp,/scratch \
    ${BATCH_SIF} \
    python /etp/ir_traffic_batch.py \
        --date ${CURRENT_DATE} \
        --output-dir /output \
        --geo-field netacq_country \
        --country IR \
        --cores ${SLURM_CPUS_PER_TASK} \
        --memory 12g
