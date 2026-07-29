[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [PySpark & Parquet](PySpark-Parquet.md) | Tasks ⮕ | [Task 1](Task-1-aggregate-daily-traffic.md) | [Task 2](Task-2-daily-churn.md) | [Task 3](Task-3-batch-job.md) | [Task 4](Task-4-full-period-analysis.md) | [Prototype Notebook](ir_traffic_prototype.ipynb) | [Analysis Notebook](analysis.ipynb)

# Tasks

Complete the tasks below in order. Tasks 1 and 2 are completed inside [ir_traffic_prototype.ipynb](ir_traffic_prototype.ipynb); Task 4 is completed inside [analysis.ipynb](analysis.ipynb). In both notebooks, replace the `# YOUR CODE HERE` sections with your code and answer the questions in the markdown cells that follow. Task 3 has no notebook code to write - it is a batch job you submit and monitor on Expanse - but its question (Q3) has its own markdown cell near the end of [ir_traffic_prototype.ipynb](ir_traffic_prototype.ipynb), just before `spark.stop()`.

## Task 0: Get access to SDSC Expanse and launch an interactive Jupyter session

- step 1. Get access to Expanse per your course's access instructions, and clone this repository there.
- step 2. Launch an interactive Jupyter session (`galyleo launch`) and open `ir_traffic_prototype.ipynb`.
- step 3. Confirm `UCSD_NT_S3_ACCESS_KEY` / `UCSD_NT_S3_SECRET_KEY` / `ETP26_ACCOUNT` are set in your shell (see [Datasets](Datasets.md)).

## Task 1: Identify IR-Geolocated Sources and Aggregate Daily Traffic

For each of the two test days, load that day's FlowTuple files into Spark, filter to rows geolocated to Iran (`netacq_country == 'IR'`), and compute: the daily totals (total packets, unique source IPs, unique ASNs), the distinct `(src_ip, prefix2asn)` pairs seen that day, the total packets contributed by each ASN that day, and a per-hour breakdown (total packets, unique ASNs) for an hourly traffic trend. See the [Task 1 Guide](Task-1-aggregate-daily-traffic.md) for the Spark aggregation patterns you'll need.

- [ ] Q1: Compare the daily summary (total packets, unique source IPs, unique ASNs) between the two test days. How much do they vary day to day, and what does that suggest about how stable this baseline "background" telescope traffic is?

## Task 2: Day-Over-Day Churn at `/24` Granularity

Aggregate each test day's IR-geolocated source IPs to their containing `/24` subnet (paired with the ASN observed for that subnet), then compute which `(subnet_24, prefix2asn)` pairs were present on the earlier test day but no longer observed on the following day. See the [Task 2 Guide](Task-2-daily-churn.md) for the set-difference pattern you'll need.

- [ ] Q2: Why look at churn in terms of `/24` subnets rather than individual source IPs or whole ASNs? What real-world explanations (besides a country-wide outage) could cause a `/24` to "disappear" for a day?

## Task 3: Scale Up to the Full Period via a Slurm Batch Job

Running Task 1's per-day logic interactively, once per day, for all ~24 days would tie up a shared interactive allocation for a very long time. Port Task 1's logic (loading a day's FlowTuple files, filtering to IR, computing the daily summary / distinct src-ip-ASN pairs / per-ASN packet totals) into `ir_traffic_batch.py`, a standalone script that takes `--date YYYY-MM-DD` and `--output-dir` and writes the same three Parquet files Task 1 does for one day. Follow the batch-job pattern from the [`3_running_batch_job`](https://github.com/CAIDA/nids-expanse-2026/tree/main/3_running_batch_job) tutorial (same Singularity container, same general script shape). See the [Task 3 Guide](Task-3-batch-job.md) for the prototype-to-batch porting pattern, including where it intentionally differs from Task 1. `run_ir_traffic.slurm` is already provided as a Slurm **job array** with one task per day, `2026-02-10` (task 0) through `2026-03-05` (task 23), each running `ir_traffic_batch.py` for its one day - the only line you need to edit is the mail-notification address (step 2 below). To keep the total data volume manageable across all 24 days, have each task sample only the **00:00 UTC hour** (12 five-minute files) of its day, rather than the full day.

- step 1. Fill in the `# YOUR CODE HERE` section of `ir_traffic_batch.py`.
- step 2. Edit the `#SBATCH --mail-user=YOUR_EMAIL_HERE` line in `run_ir_traffic.slurm` to add your own email address, enabling the email notification when the jobs `BEGIN` and `END`. From the repository root on an Expanse login node: `sbatch run_ir_traffic.slurm`
- step 3. Check progress with `squeue -u <username>`. Logs land in `joblogs/slurm-<array_job_id>_<array_task_id>.out`.
- step 4. Once all 24 tasks finish, note the array job id printed in the logs' output directory (`/expanse/lustre/projects/<project>/<username>/output/ir_traffic/<array_job_id>/`) - you'll need it for Task 4's `JOBID`.

- [ ] Q3: Use your email notification to estimate the job run time. Inspect the configuration of the slurm script. It used array of jobs (one per day). How does the array of jobs help speed up the processing comparing to the Jupyter Notebook approach?

## Task 4: Full-Period Analysis

In `analysis.ipynb`, set `JOBID` in the environment-variables cell to the array job id from Task 3, then complete:

- **Top ASNs**: rank ASNs by total packet count, and separately by number of distinct `/24` prefixes, across the two test-window days.
- **Hourly trend**: plot the hourly total-packet and unique-ASN trend from Task 1's `ir_hourly_packets_test.parquet`.
- **Full-period trend**: plot daily total packets across the whole 24-day period, and identify which day(s) show a sharp drop compared to the previous day.

See the [Task 4 Guide](Task-4-full-period-analysis.md) for the pandas patterns behind these three computations.

- [ ] Q4: Are the top 5 ASNs by packet count the same as the top 5 by distinct `/24` count? What would it mean for an ASN to rank high on one metric but not the other?
- [ ] Q5: Is there a diurnal (day/night) pattern in the hourly trend? Is it driven by a few ASNs sending more traffic at certain hours, or by more/fewer distinct ASNs being active - and does it line up with Iran's local time (UTC+3:30)?
- [ ] Q6: Read the [2026 Internet blackout in Iran](https://en.wikipedia.org/wiki/2026_Internet_blackout_in_Iran) Wikipedia article. Do the day(s) you flagged as a traffic drop fall within the blackout dates it reports? Does the size/duration of your measured drop match how the article describes the blackout's severity?

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [PySpark & Parquet](PySpark-Parquet.md) | Tasks ⮕ | [Task 1](Task-1-aggregate-daily-traffic.md) | [Task 2](Task-2-daily-churn.md) | [Task 3](Task-3-batch-job.md) | [Task 4](Task-4-full-period-analysis.md) | [Prototype Notebook](ir_traffic_prototype.ipynb) | [Analysis Notebook](analysis.ipynb)
