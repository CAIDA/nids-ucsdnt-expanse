# Review summary — nids-ucsdnt-expanse

Content and URL review of the module before it goes out to students. Nothing has been changed
yet. Agent-facing detail with file:line anchors is in [review-checkpoint.md](review-checkpoint.md).

## Bottom line

**The links are fine.** All 111 internal links and all 9 external URLs resolve. The Wikipedia
blackout article exists and is a real article, the CAIDA tutorial path is live, and the
`hermes.caida.org` 404 is just an S3 endpoint with nothing at its root — not a broken link.

**The content is not fine.** Three defects will break a student's run, one of them silently.
Beyond those, the documentation describes output files the code does not produce. Five things
below need your judgment before I touch them.

## What breaks a student run

### 1. The Slurm job fails before it starts, with no log explaining why

This is the one to fix first. `run_ir_traffic.slurm` writes its logs to `joblogs/`, but that
directory isn't in the repo — a fresh clone doesn't have it. Slurm creates the output file the
moment a task starts, *before* the script body runs, so the `mkdir -p joblogs` inside the script
never gets a chance. All 24 array tasks fail immediately.

The cruel part: because the failure is in creating the log file, there is no log. A student sees
24 failed jobs and nothing to read. Fix is trivial — commit a `joblogs/.gitkeep` and add
`mkdir -p joblogs` to the instructions before `sbatch`.

### 2. Both notebooks read a file out of someone else's directory

`ir_traffic_prototype.ipynb` and `analysis.ipynb` both contain:

```
%dotenv /expanse/lustre/projects/sdp178/kmok/.ucsdnts3.env
```

That's a hardcoded path into user `kmok`'s project directory. It works only as long as that
directory exists and stays readable. There are three different locations for this same file
across the repo — this one, the per-student path in the Slurm script, and "preloaded in your
shell" in `Datasets.md`. We agreed on the per-student path to match the Slurm script.

Also worth noting: `analysis.ipynb` loads these S3 credentials and then never touches S3. That
cell can go entirely.

### 3. The Slurm account is hardcoded, and the docs say it isn't

The script pins `--account=sdp178` while using `${ETP26_ACCOUNT}` everywhere else. Both
`Tasks.md` and the Task 3 guide tell students the mail-notification address is *the only* line
they need to edit. Any student on a different account is stuck with a wrong statement and a
second edit nobody mentioned. `REPO_DIR` has the same problem — it assumes the repo was cloned
to `/home/$USER/nids-ucsdnt-expanse`.

## Where the docs and the code disagree

**The `Datasets.md` output table is wrong about Task 1.** It says the three per-day Parquet
files are "Produced by Tasks 1 & 3". They aren't. The prototype notebook writes five files, all
suffixed `_test`; only the batch script writes the `_<date>` files. `analysis.ipynb` reads the
`_test` names, so the code is self-consistent — it's the table that's off. It needs to be split
into a prototype section and a batch section.

**One output file has an extra undocumented column.** In the prototype notebook, the Task 2 cell
adds a `subnet_24` column to `ir_src_asn_df` in place, and a later cell writes that DataFrame
out. So `ir_src_asn_test.parquet` has four columns where the docs promise three. Harmless in
practice, but it's exactly the kind of drift that confuses a student checking their work.

**"Full period" means 24 sampled hours, not 24 days.** The batch job deliberately samples only
the 00:00 UTC hour of each day. `Tasks.md` and the Task 3 guide say so; `Datasets.md`,
`Introduction.md`, and the `analysis.ipynb` plot titles do not. A student who compares their
full-day test-window numbers against their "full period" numbers sees an order-of-magnitude gap
with nothing in the docs to explain it.

## Decisions I need from you

### A. How should students set the Slurm account?

`#SBATCH` lines are parsed by Slurm before the shell runs, so `--account=${ETP26_ACCOUNT}`
cannot work — that's why it's hardcoded in the first place.

- **Option 1 (recommended):** leave the line but document `sbatch --account=$ETP26_ACCOUNT run_ir_traffic.slurm`.
  The variable is already in their shell, the CLI flag overrides the file, and students edit
  nothing.
- **Option 2:** change it to `YOUR_ACCOUNT_HERE` like the email line, and update both docs to say
  there are two edits.

Either way the "only line you need to edit" sentence has to change in two files.

### B. The batch job samples Iran's quietest hour — is that intended?

00:00 UTC is **03:30 in Iran** (IRST, UTC+3:30). So the full-period analysis samples the middle
of the night, every single day.

This creates an odd sequence: Q5 asks students to find the diurnal day/night pattern in the
hourly data, and then Q6 asks them to detect a national blackout using a daily sample taken at
the trough of exactly that pattern. It's defensible — a blackout should still show up — but a
sharp student will notice, and right now nothing in the module acknowledges it.

You already said keep the sampling and document it, which I think is right. Flagging it once
more because it's a teaching decision, not a mechanical one: if the blackout signal turns out
weak in a test run, the sampled hour is the first thing to revisit.

### C. Where should the combined Parquet files go, and do you want a `.gitignore`?

`analysis.ipynb` writes its three combined files with bare relative paths, so they land in the
cloned repo. `Datasets.md` explicitly says output belongs on Lustre, not the home directory —
so the code contradicts the docs.

There's no `.gitignore` in the repo, and README step 9 tells students to commit and push. As it
stands they'll commit Parquet output, `joblogs/`, and `.ipynb_checkpoints/`. I'd write the
combined files to `output/full/` on Lustre and add a `.gitignore`, but the `.gitignore` in
particular is your call since it affects what you see in their submissions.

### D. Should the `Datasets.md` example values be realistic?

The FlowTuple field table reads as one example record with `netacq_country = IR`, but
`src_ip 3229923820` decodes to `192.132.185.236` and `prefix2asn` is `1756` — neither is
Iranian. The `time` value is correct (2026-02-14 00:00 UTC, the first test day).

Low stakes. Swap in a real Iranian IP and ASN, or leave them as obviously-illustrative values?

### E. Is it OK to hand students five variable names?

The Task 1 loop in the prototype notebook ends with a line *outside* the `# YOUR CODE HERE`
block:

```python
del spark_df, ir_df, src_asn_rows, asn_rows, hourly_rows
```

Nothing tells students to use those five names. The nine TODO steps don't mention them and the
Task 1 guide only ever shows `spark_df` and `ir_df`. Any student who names their variables
anything else gets a `NameError` at the end of a loop that otherwise worked.

The easy fix is to name all five in the TODO comments — but that's more scaffolding than the
rest of the task gives. The alternative is restructuring the cell so the cleanup isn't exposed
to students at all. Your call on how much freedom the task should leave.

## Needs an Expanse run to settle

I can't verify these from here, so I'm reporting rather than changing them:

- **Spark/Hadoop version pairing.** Both the notebook and the batch script pin
  `spark-avro_2.13:4.2.0` alongside `hadoop-aws:3.5.0`. `hadoop-aws` has to match the Hadoop
  version bundled in the container's Spark build, or S3A fails with `NoSuchMethodError`. Worth
  confirming against the actual `.sif`.
- **Memory headroom is tight.** The Slurm job requests 4 CPUs × 4000 MB ≈ 15.6 GiB, and gives
  Spark a 12g heap. That leaves ~3.6 GiB for JVM metaspace, off-heap, the container, and Python.
  Probably fine, but one real run would confirm it before 24 tasks hit it at once.

## Polish backlog — no decisions needed

| Where | Fix |
|---|---|
| `README.md` glossary | "Backscatter" is used to define *all* unsolicited telescope traffic, then the next sentence correctly lists it as one of four categories. Drop the parenthetical. |
| `README.md` glossary | Entry is titled `netacq_country` but describes two fields — should name `maxmind_country` too. |
| `README.md` directory tree | Lists `joblogs/` (created at submit time) but omits `slides/`, which the README links two sections earlier. |
| `Introduction.md` | Two typos: "backout" → "blackout", "disappearence" → "disappearance". |
| `PySpark-Parquet.md` | Describes the module as running `local[*]`, but the prototype pins `local[N]` from `SLURM_CPUS_PER_TASK` and the Slurm script always passes `--cores`. The point being made is still right — just reword to "local mode". Lowest priority item on this list. |
| `Tasks.md` | Says `ETP26_ACCOUNT` is documented in `Datasets.md`. It isn't — only the two S3 keys are. |
| Q3 wording | "It used array of jobs (one per day)" → "It uses a job array (one task per day)". Appears verbatim in three places (`Tasks.md`, Task 3 guide, prototype notebook) and must be fixed in all three. |
