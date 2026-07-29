[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [PySpark & Parquet](PySpark-Parquet.md) | [Tasks](Tasks.md) | [Task 1](Task-1-aggregate-daily-traffic.md) | Task 2 ⮕ | [Task 3](Task-3-batch-job.md) | [Task 4](Task-4-full-period-analysis.md) | [Prototype Notebook](ir_traffic_prototype.ipynb) | [Analysis Notebook](analysis.ipynb)

# Task 2 Guidance: Day-Over-Day Churn at `/24` Granularity

This guides the second `# YOUR CODE HERE` section in `ir_traffic_prototype.ipynb`. Task 1 gave you `ir_src_asn_df`: the distinct `(src_ip, prefix2asn)` pairs geolocated to IR for each test day. Task 2 asks a different question - not *how much* traffic, but *which* address space stopped showing up between the two test days.

### Bucketing Source IPs to `/24`

Individual source IPs can be dynamically reassigned by an ISP day to day, which is noisy for detecting real disappearance. The already-provided helper collapses a dotted-quad IP down to its containing `/24`:

```python
def ip_to_slash24(ip):
    return '.'.join(ip.split('.')[:3]) + '.0/24'
```

### Building the Per-Day Subnet/ASN Set

Apply that helper to every row of `ir_src_asn_df`, then collapse to distinct `(subnet_24, prefix2asn)` pairs per day - many individual IPs in the same `/24` collapse to one row:

```python
ir_src_asn_df['subnet_24'] = ir_src_asn_df['src_ip'].apply(ip_to_slash24)
ir_subnet24_asn_df = ir_src_asn_df[['date', 'subnet_24', 'prefix2asn']].drop_duplicates()
```

This reuses Task 1's output directly - there's no new Spark work in Task 2, it's all pandas.

### Looping Over Consecutive Day Pairs

With only two test days there's one pair, but the loop is written generally so it also works once you add more dates:

```python
for prev_date, next_date in zip(sorted_test_dates[:-1], sorted_test_dates[1:]):
```

### Set Difference to Find What Disappeared

For each `(prev_date, next_date)` pair, pull each day's set of `(subnet_24, prefix2asn)` pairs and take the set difference - what was present on `prev_date` but absent on `next_date`:

```python
prev_pairs = set(map(tuple, ir_subnet24_asn_df.loc[
    ir_subnet24_asn_df['date'] == prev_date, ['subnet_24', 'prefix2asn']
].itertuples(index=False, name=None)))
next_pairs = set(map(tuple, ir_subnet24_asn_df.loc[
    ir_subnet24_asn_df['date'] == next_date, ['subnet_24', 'prefix2asn']
].itertuples(index=False, name=None)))

missing_pairs = sorted(prev_pairs - next_pairs)
```

Converting each day's rows to a `set` of tuples (rather than comparing DataFrames directly) is what makes `-` do a real set difference.

### Assembling and Appending the Result

Turn `missing_pairs` back into a DataFrame, tag it with which day pair it came from, and append it to the list that gets concatenated after the loop:

```python
disappeared_subnet24_frames.append(pd.DataFrame(
    missing_pairs, columns=['subnet_24', 'prefix2asn']
).assign(prev_date=prev_date, next_date=next_date))
```

### What Your Write-Up Should Address

- [ ] Q2: Why look at churn in terms of `/24` subnets rather than individual source IPs or whole ASNs? What real-world explanations (besides a country-wide outage) could cause a `/24` to "disappear" for a day?

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [PySpark & Parquet](PySpark-Parquet.md) | [Tasks](Tasks.md) | [Task 1](Task-1-aggregate-daily-traffic.md) | Task 2 ⮕ | [Task 3](Task-3-batch-job.md) | [Task 4](Task-4-full-period-analysis.md) | [Prototype Notebook](ir_traffic_prototype.ipynb) | [Analysis Notebook](analysis.ipynb)
