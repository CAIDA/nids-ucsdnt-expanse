[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [PySpark & Parquet](PySpark-Parquet.md) | [Tasks](Tasks.md) | [Task 1](Task-1-aggregate-daily-traffic.md) | [Task 2](Task-2-daily-churn.md) | [Task 3](Task-3-batch-job.md) | Task 4 ⮕ | [Prototype Notebook](ir_traffic_prototype.ipynb) | [Analysis Notebook](analysis.ipynb)

# Task 4 Guidance: Full-Period Analysis

This guides the three `# YOUR CODE HERE` sections in `analysis.ipynb`. By this point Spark is done - Tasks 1-3 already wrote everything to Parquet, so all of Task 4 is plain pandas over the files `analysis.ipynb` loads at the top of Part A and Part B. Before running Part B, set `JOBID` in the notebook's environment-variables cell to your Task 3 array job id - `BATCH_OUTPUT_DIR`'s load cell won't find any files until you do.

### Top 5 ASNs by Packet Count

Using `asn_daily_packet_df` (the per-ASN, per-day packet totals from Task 1/3), sum across days per ASN, then take the top 5:

```python
top5_asn_by_packets = (
    asn_daily_packet_df.groupby('prefix2asn')['total_packet_cnt']
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .rename('total_packet_cnt')
    .reset_index()
)
```

### Top 5 ASNs by Distinct `/24` Count

This reuses the same `ip_to_slash24` bucketing from the [Task 2 Guide](Task-2-daily-churn.md) - see that guide for why `/24` is the right granularity. Here you're not diffing days, just counting how many distinct `/24`s each ASN touched across the whole window:

```python
ir_src_asn_df['subnet_24'] = ir_src_asn_df['src_ip'].apply(ip_to_slash24)
subnet24_asn_df = ir_src_asn_df[['subnet_24', 'prefix2asn']].drop_duplicates()

top5_asn_by_subnet24 = (
    subnet24_asn_df.groupby('prefix2asn')['subnet_24']
    .nunique()
    .sort_values(ascending=False)
    .head(5)
    .rename('distinct_slash24_count')
    .reset_index()
)
```

Q4 asks you to compare this ranking against the packet-count ranking above - an ASN can be small on one metric and large on the other (e.g. few `/24`s each sending a lot of traffic, vs. many `/24`s each sending a little).

### Flagging Drop Days

`full_daily_summary_df` (loaded from Task 3's per-day batch output in Part B) has one row per day across the whole ~24-day period. `pct_change()` computes each day's fractional change versus the previous row:

```python
DROP_THRESHOLD = 0.5  # flag a day if its traffic falls by more than 50% vs. the previous day

full_daily_summary_df['pct_change_from_prev_day'] = (
    full_daily_summary_df['total_packet_cnt'].pct_change()
)

drop_days_df = full_daily_summary_df[full_daily_summary_df['pct_change_from_prev_day'] < -DROP_THRESHOLD]
```

Note the sign: a drop shows up as a *negative* `pct_change`, so the filter compares against `-DROP_THRESHOLD`, not `DROP_THRESHOLD`. The first row of the full period has no previous day to compare against, so `pct_change()` leaves it `NaN` - `NaN < -0.5` is `False`, so it's correctly never flagged as a drop.

### What Your Write-Up Should Address

- [ ] Q4: Are the top 5 ASNs by packet count the same as the top 5 by distinct `/24` count? What would it mean for an ASN to rank high on one metric but not the other?
- [ ] Q5: Is there a diurnal (day/night) pattern in the hourly trend? Is it driven by a few ASNs sending more traffic at certain hours, or by more/fewer distinct ASNs being active - and does it line up with Iran's local time (UTC+3:30)?
- [ ] Q6: Read the [2026 Internet blackout in Iran](https://en.wikipedia.org/wiki/2026_Internet_blackout_in_Iran) Wikipedia article. Do the day(s) you flagged as a traffic drop fall within the blackout dates it reports? Does the size/duration of your measured drop match how the article describes the blackout's severity?

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [PySpark & Parquet](PySpark-Parquet.md) | [Tasks](Tasks.md) | [Task 1](Task-1-aggregate-daily-traffic.md) | [Task 2](Task-2-daily-churn.md) | [Task 3](Task-3-batch-job.md) | Task 4 ⮕ | [Prototype Notebook](ir_traffic_prototype.ipynb) | [Analysis Notebook](analysis.ipynb)
