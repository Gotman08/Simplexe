# Romeo deployment helpers

This directory preserves the coursework scripts for copying the project to the URCA Romeo cluster, submitting a SLURM job and retrieving results. No cluster access, job submission or resource measurement was performed for the repository overhaul.

## Configuration

Review the cluster hostname, destination, available modules and SLURM partition for your account before using the scripts. The example values below are configuration placeholders.

```bash
export ROMEO_USER=your_login
export ROMEO_HOST=romeo.univ-reims.fr
export ROMEO_DEST=/home/$ROMEO_USER/chps0805
bash Romeo/deploy.sh
ssh "$ROMEO_USER@$ROMEO_HOST"
```

On the cluster, enter the destination directory and inspect `Romeo/job_benchmark.sbatch` before running `sbatch Romeo/job_benchmark.sbatch`. Its resource directives are requests, not evidence of application parallelism or measured memory use. Adapt the commented module setup to the cluster's installed software.

From the local checkout, `bash Romeo/fetch_results.sh` retrieves output to `Resultats_romeo/`. The scripts use SSH and rsync; they do not provide credentials.

## Scope of validation

The [local verification](../docs/results.md) covers C and Python under Ubuntu WSL2. It does not establish that the original deployment scripts or historical benchmark pipeline work on the current Romeo installation. Historical figures and timings remain in `Resultats/` for context.
