[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | PySpark & Parquet ⮕ | [Tasks](Tasks.md) | [Task 1](Task-1-aggregate-daily-traffic.md) | [Task 2](Task-2-daily-churn.md) | [Task 3](Task-3-batch-job.md) | [Task 4](Task-4-full-period-analysis.md) | [Prototype Notebook](ir_traffic_prototype.ipynb) | [Analysis Notebook](analysis.ipynb)

# PySpark & Parquet Guide: What's Different in This Module

This page assumes you've already completed `nids-dns-ecosystem` and its `Spark.md` guide - SparkSession setup, filtering/selecting, groupBy/agg, joins, and broadcast variables all carry over unchanged. It covers only what's genuinely different here: the input format, running Spark on a single HPC node instead of a cluster, and the Parquet handoff between this module's scripts.

### Avro, Not Parquet

`nids-dns-ecosystem` reads OpenINTEL's data as Parquet, which supports column and predicate pushdown - Spark can skip whole row groups or columns a query doesn't need without decoding them. FlowTuple data is stored as **Avro**, which has no such pushdown: the *entire* content of a file must be decoded before a filter like `netacq_country == 'IR'` can drop the rows that don't match. This is why loading a day's ~288 five-minute files is comparatively expensive even though the IR-geolocated subset is a small fraction of the total traffic.

Reading Avro requires an extra Spark package alongside the S3A connector already familiar from `Spark.md`:

```python
'spark.jars.packages': 'org.apache.spark:spark-avro_2.13:4.2.0,org.apache.hadoop:hadoop-aws:3.5.0',
```

### Running Spark Locally on One HPC Node

`nids-dns-ecosystem` also runs `local[*]`, but here it matters more: this module runs entirely on a single Expanse compute node (interactively via `galyleo launch`, or one node per Slurm array task) rather than a distributed cluster, so `local[*]` mode runs the driver *and* every "executor" in one JVM process. That makes `spark.driver.memory` the real ceiling on how much data a query can touch at once - left unset, Spark defaults to ~1g, which OOM-kills the JVM after a file or two. The prototype notebook sizes this explicitly:

```python
('spark.driver.memory', '24g'),
('spark.driver.maxResultSize', '4g'),
('spark.sql.shuffle.partitions', '100'),  # default 200 is excessive overhead for 4 local cores
```

Keep `spark.driver.memory` comfortably below whatever memory you actually requested for the session (e.g. `galyleo launch --memory 32`), leaving headroom for the Python driver process, OS, and Jupyter itself. The batch script (`ir_traffic_batch.py`) uses the same pattern but smaller - `--memory 12g` and `shuffle.partitions=32` - since each invocation only processes one sampled hour of one day, not a full day.

If you see `"SparkContext was shut down"` or `"Connection refused"`, that's the whole JVM getting OOM-killed by the OS/cgroup, not an ordinary catchable Spark error - the kernel needs a full restart, since re-running cells reuses a dead py4j connection.

### `.collect()` vs. `.toPandas()`

`Spark.md` uses `.toPandas()` throughout to pull small, already-aggregated results back to the driver. The prototype notebook here uses raw `.collect()` on similarly small aggregates instead, specifically to avoid an Arrow-based `.toPandas()` conversion crash in this runtime (see the [Task 1 Guide](Task-1-aggregate-daily-traffic.md)) - Arrow is disabled entirely (`spark.sql.execution.arrow.pyspark.enabled: false`).

The batch script uses `.toPandas()` instead, because each invocation's result is even smaller - one day, one sampled hour - and needs to end up as a DataFrame ready for `.to_parquet()` (see the [Task 3 Guide](Task-3-batch-job.md)). `.collect()` returns a list of Spark `Row` objects, which still need to be converted to a DataFrame by hand; `.toPandas()` skips that step when Arrow isn't in the way.

### Cleaning Up Between Loop Iterations

`Spark.md`'s queries are one-shot - load, filter, aggregate, done. This module's Task 1 loop instead runs the same query shape once per day, in the same long-lived local Spark session, and Spark accumulates cached query plans and broadcast state across those iterations. Left unchecked, that compounds into an out-of-memory error partway through the loop, so each iteration ends with:

```python
del spark_df, ir_df, src_asn_rows, asn_rows, hourly_rows
spark.catalog.clearCache()
gc.collect()
```

The batch script doesn't need this - each Slurm array task starts a fresh Spark session for exactly one day and exits.

### The Parquet Write/Read Handoff

This module splits into a Spark stage (prototype notebook, batch script) that writes Parquet, and a pandas-only stage (`analysis.ipynb`) that reads it back - no Spark session at all in `analysis.ipynb`. This decouples the heavy S3/Avro-decoding work from the lightweight analysis/plotting work, and lets Task 3's batch job run unattended across the full period without holding a Jupyter session open the whole time.

The handoff itself uses plain pandas, not `pyarrow` directly the way `nids-telescope-traffic`'s `Pyarrow.md` does - writing is `df.to_parquet(path, index=False)` and reading is `pd.read_parquet(path)`, so `analysis.ipynb` needs no extra library beyond pandas itself.

### Best Practices, All Together

- **Avro has no pushdown** - filter as early as possible after loading, and don't re-filter the same day's data more than once (reuse `ir_df` for all four Task 1 outputs).
- **Size `spark.driver.memory` to your actual allocation**, with headroom for the OS/driver - not the Spark default.
- **`.collect()` when Arrow conversion is unreliable, `.toPandas()` otherwise** - use whichever the surrounding code already uses for that notebook/script, don't mix conventions within one file.
- **Clear Spark's cache between loop iterations** in any long-lived local session that runs the same query shape repeatedly.
- **Write Parquet from Spark, read Parquet with pandas** once the aggregation is done - don't keep a Spark session alive just to read back your own output.

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | PySpark & Parquet ⮕ | [Tasks](Tasks.md) | [Task 1](Task-1-aggregate-daily-traffic.md) | [Task 2](Task-2-daily-churn.md) | [Task 3](Task-3-batch-job.md) | [Task 4](Task-4-full-period-analysis.md) | [Prototype Notebook](ir_traffic_prototype.ipynb) | [Analysis Notebook](analysis.ipynb)
