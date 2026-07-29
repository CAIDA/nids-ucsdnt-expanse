[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [PySpark & Parquet](PySpark-Parquet.md) | [Tasks](Tasks.md) | Task 1 ⮕ | [Task 2](Task-2-daily-churn.md) | [Task 3](Task-3-batch-job.md) | [Task 4](Task-4-full-period-analysis.md) | [Prototype Notebook](ir_traffic_prototype.ipynb) | [Analysis Notebook](analysis.ipynb)

# Task 1 Guidance: Aggregating One Day of IR-Geolocated Traffic

This provides a guide to implementing the per-day loop body in Task 1 of `ir_traffic_prototype.ipynb`. Your goal is, for a single day, to go from a Spark DataFrame of that day's FlowTuple records to four things: a daily summary, a distinct source-IP/ASN list, packets-per-ASN, and packets-per-hour - all filtered to rows geolocated to Iran.

### Loading and Filtering One Day

Two helper functions are already provided above this cell:

- `time_to_avro_list(s3_objects_df, start_time, end_time)` - returns the S3A paths for one day's Avro files.
- `load_ft_pyspark(avro_files)` - reads those files into a Spark DataFrame with `time` normalized to UTC.

Filtering to IR-geolocated rows is a single Spark `filter`:

```python
ir_df = spark_df.filter(F.col(GEO_FIELD) == GEO_COUNTRY)
```

Do this filter **once** per day and reuse `ir_df` for all four outputs below - re-filtering separately for each output would mean Spark re-reads and re-decodes the Avro files multiple times.

### Null-Safe Aggregation

`packet_cnt` should always be present, but summing over an empty DataFrame (e.g. a day with zero IR-geolocated rows) returns `null` rather than `0`. Wrap sums in `F.coalesce(..., F.lit(0))` so downstream Parquet consumers always see a numeric total:

```python
F.coalesce(F.sum('packet_cnt'), F.lit(0)).alias('total_packet_cnt')
```

### The Four Outputs

1. **Daily summary** - one row of aggregates, pulled back to the driver with `.agg(...).collect()[0]` (avoids the Arrow-based `toPandas()` conversion, which can crash this runtime):

   ```python
   summary = ir_df.agg(
       F.coalesce(F.sum('packet_cnt'), F.lit(0)).alias('total_packet_cnt'),
       F.countDistinct('src_ip').alias('unique_src_ips'),
       F.countDistinct('prefix2asn').alias('unique_asns'),
   ).collect()[0]
   ```

2. **Distinct source IP / ASN pairs** - `ir_df.select('src_ip', 'prefix2asn').distinct().collect()`, then convert `src_ip` from its packed-integer form back to a dotted-quad string with the provided `long2ip()` helper.

3. **Packets per ASN** - a `groupBy('prefix2asn')` with the same coalesced sum:

   ```python
   ir_df.groupBy('prefix2asn').agg(
       F.coalesce(F.sum('packet_cnt'), F.lit(0)).alias('total_packet_cnt')
   ).collect()
   ```

4. **Packets and unique ASNs per hour** - same idea, but group by an hour-truncated timestamp instead of ASN:

   ```python
   ir_df.groupBy(
       F.date_trunc('hour', F.col('time')).alias('hour')
   ).agg(
       F.coalesce(F.sum('packet_cnt'), F.lit(0)).alias('total_packet_cnt'),
       F.countDistinct('prefix2asn').alias('unique_asns'),
   ).collect()
   ```

### Cleaning Up Between Days

The loop processes each day independently, but Spark accumulates cached query plans and broadcast state across iterations in `local[*]` mode. Before moving to the next day, release this day's DataFrames and clear Spark's cache so that state doesn't compound into an out-of-memory error over a long loop:

```python
del spark_df, ir_df, src_asn_rows, asn_rows, hourly_rows
spark.catalog.clearCache()
gc.collect()
```

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [PySpark & Parquet](PySpark-Parquet.md) | [Tasks](Tasks.md) | Task 1 ⮕ | [Task 2](Task-2-daily-churn.md) | [Task 3](Task-3-batch-job.md) | [Task 4](Task-4-full-period-analysis.md) | [Prototype Notebook](ir_traffic_prototype.ipynb) | [Analysis Notebook](analysis.ipynb)
