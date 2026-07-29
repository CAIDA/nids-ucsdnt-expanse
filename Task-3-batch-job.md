[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [PySpark & Parquet](PySpark-Parquet.md) | [Tasks](Tasks.md) | [Task 1](Task-1-aggregate-daily-traffic.md) | [Task 2](Task-2-daily-churn.md) | Task 3 ⮕ | [Task 4](Task-4-full-period-analysis.md) | [Prototype Notebook](ir_traffic_prototype.ipynb) | [Analysis Notebook](analysis.ipynb)

# Task 3 Guidance: Porting the Prototype into a Batch Job

This guides the `# YOUR CODE HERE` section in `ir_traffic_batch.py`'s `main()`. There's no notebook code cell for Task 3 (its question has a markdown answer cell near the end of `ir_traffic_prototype.ipynb` instead) - you're porting Task 1's per-day logic into a standalone script that runs once per day as a Slurm array task.

### Reusing the Already-Provided Scaffolding

`ir_traffic_batch.py` already gives you everything Task 1's notebook cells built individually: `long2ip`, `load_ft_pyspark`, `time_to_avro_list`, `list_avro_objects`, argument parsing (`parse_args`), and the SparkConf/session setup. You're only filling in the aggregation logic itself, at the bottom of `main()`.

### Sampling Only the 00:00 UTC Hour

Task 1's prototype loads a full day per test day. Running that for all ~24 days in the full period would be far more data than this module needs to demonstrate the pipeline, so the batch job deliberately samples just the first hour of each day:

```python
day_start = day.normalize()
day_end = day_start + pd.Timedelta(minutes=55)
```

This is different from Task 1's `pd.Timedelta(hours=23, minutes=55)` - that's intentional, not something to "fix" to match Task 1.

### Filtering via CLI Args, Not Hardcoded Globals

Task 1 filters against the module-level `GEO_FIELD`/`GEO_COUNTRY` constants. The batch script instead takes these as command-line arguments (`--geo-field`, `--country`) so the same script can be re-run for a different country or geolocation source without editing code:

```python
ir_df = spark_df.filter(F.col(args.geo_field) == args.country)
```

The `F.coalesce(F.sum('packet_cnt'), F.lit(0))` null-safety pattern from the [Task 1 Guide](Task-1-aggregate-daily-traffic.md) still applies here - reuse it rather than re-deriving it.

### `.toPandas()` Instead of `.collect()`, Plus the `date` Column

Task 1's prototype collects each aggregate with `.collect()` to sidestep an Arrow conversion issue (see [PySpark & Parquet](PySpark-Parquet.md) for why). The batch script uses `.toPandas()` instead, because each invocation's result is already small - one day, one sampled hour - and a `DataFrame` is what `.to_parquet()` needs:

```python
summary_row = ir_df.agg(
    F.coalesce(F.sum('packet_cnt'), F.lit(0)).alias('total_packet_cnt'),
    F.countDistinct('src_ip').alias('unique_src_ips'),
    F.countDistinct('prefix2asn').alias('unique_asns'),
).toPandas()
summary_row.insert(0, 'date', args.date)
```

Every output DataFrame needs that same `.insert(0, 'date', args.date)` (or equivalent) - unlike the prototype notebook, where one loop produces all test days at once, each batch invocation only ever knows about its own single day, so the `date` column has to be added explicitly rather than coming from a groupby. For the per-ASN table, also sort so the largest contributors come first: `.sort_values('total_packet_cnt', ascending=False)`.

### Writing the Three Output Files

Write exactly the files [Datasets.md](Datasets.md) documents, one row (or one row per ASN) per invocation:

- `ir_daily_summary_<date>.parquet`
- `ir_src_asn_<date>.parquet` (remember to convert `src_ip` back to a dotted-quad with `long2ip` before writing)
- `ir_asn_daily_packets_<date>.parquet`

### Slurm Job-Array Mechanics

`run_ir_traffic.slurm` is already complete and shouldn't need any code changes. Each of its 24 array tasks (`--array=0-23%4`) computes its own date from `SLURM_ARRAY_TASK_ID` and calls `ir_traffic_batch.py --date <that day>`, via a `singularity exec` of the same container used in the `3_running_batch_job` tutorial. The one thing you do need to edit in it is the email line - fill in `#SBATCH --mail-user=YOUR_EMAIL_HERE` with your own address so Slurm emails you when the array `BEGIN`s and `END`s; that email is what Q3 asks you to use to estimate the run time.

### What Your Write-Up Should Address

- [ ] Q3: Use your email notification to estimate the job run time. Inspect the configuration of the slurm script. It used array of jobs (one per day). How does the array of jobs help speed up the processing comparing to the Jupyter Notebook approach?

Write your answer in the **Q3** markdown cell near the end of [ir_traffic_prototype.ipynb](ir_traffic_prototype.ipynb) (just before its final `spark.stop()` cell), not in this guide.

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [PySpark & Parquet](PySpark-Parquet.md) | [Tasks](Tasks.md) | [Task 1](Task-1-aggregate-daily-traffic.md) | [Task 2](Task-2-daily-churn.md) | Task 3 ⮕ | [Task 4](Task-4-full-period-analysis.md) | [Prototype Notebook](ir_traffic_prototype.ipynb) | [Analysis Notebook](analysis.ipynb)
