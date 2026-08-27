# Review summary — nids-ucsdnt-expanse

Content and URL review of the module, cross-checked against the executed instructor key.
**No student source file has been changed.** Q6 has been fixed in the key and is waiting on a
re-run; everything else is still parked. Agent-facing detail with file:line anchors is in
[review-checkpoint.md](review-checkpoint.md).

## Bottom line

**The links are fine.** All 111 internal links and all 9 external URLs resolve. The Wikipedia
blackout article exists and is a real article, the CAIDA tutorial path is live, and the
`hermes.caida.org` 404 is just an S3 endpoint with nothing at its root — not a broken link.

**Two things would have gone out broken.** Q6's central question couldn't discriminate, and the
Slurm job fails before it starts. Q6 is now fixed in the key. The Slurm failure is fixed in the
key and still open in the student repo.

## Done: Q6 (in the key)

Q6 asked whether the flagged drop days "fall within the blackout dates reported by the article."
The article reports the blackout running **8 January – 25 May 2026** — the entire study period
sits inside it, so the answer was trivially yes for all 24 days, including the three that are
`pct_change()` artifacts rather than real events. The key's own written answer opened by calling
the comparison "close to meaningless here."

The article does contain a sharp, datable event: the **28 February renewal**, reported at ~4% of
ordinary connectivity falling to ~1% by 6 March. Your data brackets it precisely —
`unique_src_ips` 835 → 33 and `unique_asns` 92 → 11 at the 03-01 sample. Against a pre-renewal
baseline that's **2.8% of baseline source IPs, falling to 2.1% by 03-05** — sitting between the
article's two reported figures and moving the same direction. That quantitative match is the
teaching payoff the old wording threw away.

Staged in the key on `q6-change-date`:

1. **Q6 reworded** onto the 28 Feb renewal — asks for the magnitude comparison, which flagged
   days are real vs. spike rebounds, and how to state a result whose baseline is itself measured
   during a blackout. The baseline boundary comes from the article, not from peeking at the data.
2. **New `pct_of_baseline_df` cell** — provided working code, so Task 4's coding scope stays at
   three student exercises.
3. **Per-ASN cell fixed.** This one was quietly broken: it ended in `.head(10)` on a
   date-sorted frame, so it only ever returned 2026-02-14 — a false positive — and **never a
   real drop day**. The old Q6 told students to "use the table above," which was impossible.
4. **Q6 answer rewritten**, carrying a `VERIFY AFTER RE-RUN` banner. Its reasoning survives; the
   figures came from job `52586699` and need re-checking, and the per-ASN paragraph can only be
   written once the fixed cell has run.
5. **`joblogs/.gitkeep` added**, plus `README.md` and `todo.md` updated.

**Before you submit the re-run:** `joblogs/` must exist, or all 24 tasks die silently (see
below). Also confirm `--account`, `REPO_DIR`, and that `etppybatch.sif` and `.ucsdnts3.env`
exist under `USERPROJ_DIR` for whoever runs it — the last run was under `kmok`, and that path is
user-scoped.

**One bonus:** the re-run also unblocks Q3, which has been pending on a wall-clock time. Capture
`sacct -j <new_jobid> --format=JobID,Start,End,Elapsed` while the record is fresh.

## Still open in the student repo

Deliberately untouched — the student repo gets updated once, after the key is final, so the Q6
wording and cells can be copied rather than re-derived.

### The Slurm job fails before it starts, with no log

`run_ir_traffic.slurm` writes logs to `joblogs/`, but that directory isn't in the repo. Slurm
creates the output file the moment a task starts, *before* the script body runs, so the
`mkdir -p joblogs` inside the script never gets a chance. All 24 array tasks fail immediately —
and because the failure *is* creating the log file, there's nothing to read. Fixed in the key;
the student repo still needs the same `joblogs/.gitkeep`.

### Both notebooks read a file out of someone else's directory

Both contain `%dotenv /expanse/lustre/projects/sdp178/kmok/.ucsdnts3.env`. Your note that the
key ran under `kmok` corrected my earlier read: the `%dotenv` line is a *deliberate* addition for
students, not a regression — the key doesn't need it because that shell already had the
credentials. So the fix is narrower than I first said: keep `%dotenv`, just repoint it to the
student's own path. `analysis.ipynb` still loads S3 credentials it never uses; that cell can go.

### The Slurm account is hardcoded, and the docs say it isn't

`--account=sdp178` is pinned while everything else uses `${ETP26_ACCOUNT}`, and both `Tasks.md`
and the Task 3 guide tell students the mail address is *the only* line to edit. `REPO_DIR` has
the same problem — it assumes the clone lives at `/home/$USER/nids-ucsdnt-expanse`.

### The `Datasets.md` output table is wrong about Task 1

It says the three `<date>`-suffixed Parquet files are "Produced by Tasks 1 & 3." They aren't —
the prototype writes five files, all suffixed `_test`; only the batch script writes `_<date>`.
The key confirms this. The table needs splitting into a prototype section and a batch section.

Two related items **flipped** once I read the key, and are now docs-only fixes:

- `ir_src_asn_test.parquet` really does have a 4th `subnet_24` column — the key produces it too,
  so document the column rather than changing the notebook.
- The combined `ir_*_full.parquet` files really are written to the repo, not Lustre — the key
  does the same. So `Datasets.md`'s "should be stored on Lustre" line is what's wrong.

### "Full period" means 24 sampled hours, not 24 days

The batch job samples only the 00:00 UTC hour. `Tasks.md` and the Task 3 guide say so;
`Datasets.md`, `Introduction.md`, and the Part B plot titles don't. Students comparing full-day
test-window numbers against "full period" numbers see an order-of-magnitude gap with nothing
explaining it.

### The test window isn't a clean baseline

2026-02-14/15 sit inside the restricted phase — the article puts Iranian traffic at 50% of
normal as of 16 February — and **02-14 is itself one of the five flagged drop days**. Q1 asks
what the two days say about "baseline background telescope traffic," and the key's own answer
has to caveat that it's "a degraded baseline, not pre-blackout normal traffic." One sentence in
`Introduction.md` and near Q1 would fix it.

## Decisions I still need from you

**1. How should students set the Slurm account?** `#SBATCH` lines are parsed before the shell
runs, so `--account=${ETP26_ACCOUNT}` cannot work. I'd document
`sbatch --account=$ETP26_ACCOUNT run_ir_traffic.slurm` — the variable is already in their shell,
the flag overrides the file, and students edit nothing. The alternative is a second
`YOUR_ACCOUNT_HERE` placeholder. Either way the "only line you need to edit" sentence changes in
two files.

**2. Do you want a `.gitignore`?** There isn't one, and README step 9 tells students to commit
and push — so they'll commit Parquet output, `joblogs/`, and `.ipynb_checkpoints/`. Affects what
lands in their submissions, so it's your call. Note the rule needs to be `joblogs/*` plus
`!joblogs/.gitkeep`, not a bare `joblogs/`.

**3. Should the `Datasets.md` example values be realistic?** The field table reads as one record
with `netacq_country = IR`, but `src_ip 3229923820` decodes to `192.132.185.236` and
`prefix2asn` is `1756` — neither Iranian. The key's own Q4 output now gives you real ones:
**197207, 58224, 44244** (top by distinct `/24`) or **48551, 49556, 208137** (top by packets).

**4. Is it OK to hand students five variable names?** The Task 1 loop ends with
`del spark_df, ir_df, src_asn_rows, asn_rows, hourly_rows` *outside* the `# YOUR CODE HERE`
block. Nothing tells students to use those names, so anyone choosing differently gets a
`NameError` at the end of a loop that otherwise worked. The key uses exactly those five, so
naming them in the TODO comments would make student code match the key — but it is more
scaffolding than the rest of the task gives.

**5. A key answer cites guidance that doesn't exist.** Key Q5 says "extending the aggregation
loop's `groupBy` to also group by `prefix2asn` (**as the Task 4 guide suggests**)" — the Task 4
guide suggests no such thing. Either add it to the guide or the key answer is stale.

## Polish backlog — no decisions needed

| Where | Fix |
|---|---|
| `README.md` glossary | "Backscatter" is used to define *all* unsolicited telescope traffic, then the next sentence correctly lists it as one of four categories. Drop the parenthetical. |
| `README.md` glossary | Entry titled `netacq_country` but describes two fields — should name `maxmind_country` too. |
| `README.md` directory tree | Lists `joblogs/` but omits `slides/`, linked two sections earlier. |
| `Introduction.md` | Two typos: "backout" → "blackout", "disappearence" → "disappearance". |
| `PySpark-Parquet.md` | Describes the module as running `local[*]`, but the prototype pins `local[N]` and the Slurm script always passes `--cores`. The point stands — just reword to "local mode". Lowest priority here. |
| `Tasks.md` | Says `ETP26_ACCOUNT` is documented in `Datasets.md`. It isn't. |
| `Datasets.md` | `prefix2asn = 0` shows up in real data (source IPs with no resolvable origin ASN) and will appear in students' top-N rankings. Undocumented. |
| Q3 wording | "It used array of jobs (one per day)" → "It uses a job array (one task per day)". Verbatim in three places — `Tasks.md`, the Task 3 guide, and the prototype notebook. |

## Still needs a real run to settle

The `spark-avro 4.2.0` / `hadoop-aws 3.5.0` pairing (must match the Hadoop version in the
container's Spark build, or S3A throws `NoSuchMethodError`), and the memory headroom — 4 CPUs ×
4000 MB ≈ 15.6 GiB against a 12g Spark heap leaves ~3.6 GiB for JVM overhead, container, and
Python. **The key's pending re-run settles both.**
