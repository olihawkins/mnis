# Code review: `mnis` 2.0.0

Review of `src/mnis` (4,392 lines across 14 modules) carried out on 2026-08-27
against polars 1.43.2 and the live MNIS API.

Findings were verified empirically wherever possible: every function in
`mnis.__all__` was called against the live API, and the specific defects below
were reproduced in isolation. Where a defect is latent (correct against today's
data but wrong on plausible data) that is stated explicitly.

Summary of what is **not** wrong, so it can be excluded: all 40 public functions
run cleanly against the live API; the dissolution-adjustment logic in
`fetch_commons_memberships` is correct at every boundary date; the run-length
grouping in `combine_party_memberships` is correct and deterministic; the
`contacts_mps` / `contacts_lords` module pair and the `mps` / `lords` module
pair are structurally identical modulo the House substitution, so there are no
copy-paste defects between them; `ruff` reports nothing beyond two `B904`
style hits.

---

## Status

All thirteen findings have since been fixed, on the same day as the review. The
diagnosis in each section below is left as written, as the record of what was
wrong, so its line references point at the **pre-fix** code; a **Fix applied**
block at the end of each says what changed and cites current lines.

| # | Finding | Status |
| --- | --- | --- |
| 1 | Unguarded null sections crash three raw fetch functions | **Fixed** |
| 2 | `filter_memberships` keeps rows for people with no filter membership | **Fixed** |
| 3 | `filter_memberships` mis-handles null *and* duplicate membership ids | **Fixed** |
| 4 | `process_member_age` off by one on ~14% of birthdays | **Fixed** (removed) |
| 5 | `extract_username` raises `IndexError` on an empty URL | **Fixed** |
| 6 | `BasicDetails` is the only query that is never cached | **Fixed** |
| 7 | The cache has no expiry and no way to clear it | **Fixed** (no TTL) |
| 8 | `rows[0]` schema derivation fails on empty results | **Fixed** |
| 9 | `extract_data_output` raises on a uniformly-absent field | **Fixed** |
| 10 | `process_missing_values` has two unreachable branches | **Fixed** (removed) |
| 11 | `fetch_mps_blogs` / `fetch_lords_blogs` always return zero rows | **Fixed** (removed) |
| 12 | Validation order in `filters.py` lets bad arguments through | **Fixed** |
| 13 | HTTP requests have no timeout and no retry | **Fixed** |

One correction to the original review, recorded in full under finding 3: that
finding understated the problem. The nullable-id defect it described was
latent, but the same root cause has a second failure mode — **duplicate**
membership ids — which was **live**, and which the original review missed. The
fix corrects both. This is the only change so far that alters output against
today's data: 789 rows that were being wrongly retained are now excluded.

---

## 1. Unguarded null sections crash three raw fetch functions

**Severity: high (latent — will crash on data MNIS is already known to return)**
**— FIXED**

`raw_mps.py:76`, `raw_mps.py:117`, `raw_lords.py:74`

MNIS returns `null` instead of a container object for a member who has no
entries in a given data output. Most of the raw fetch functions guard against
this with a "Remove NULL" filter, e.g. `raw_lords.py:112`:

```python
party_memberships_raw = [
    member for member in party_memberships_raw
    if member.get("Parties") is not None
]
```

Three functions omit that guard and index straight into the section:

| Function | Line | Expression |
| --- | --- | --- |
| `fetch_commons_memberships_raw` | `raw_mps.py:76` | `member["Constituencies"]["Constituency"]` |
| `fetch_mps_party_memberships_raw` | `raw_mps.py:117` | `member["Parties"]["Party"]` |
| `fetch_lords_memberships_raw` | `raw_lords.py:74` | `member["HouseMemberships"]["HouseMembership"]` |

This is not hypothetical. Counting null sections in today's live responses:

```
Commons  Constituencies     members= 2739 null-section=0
Commons  Parties            members= 2739 null-section=0
Lords    HouseMemberships   members= 2808 null-section=0
Lords    Parties            members= 2808 null-section=1   <-- guarded
Commons  MaidenSpeeches     members= 2739 null-section=21  <-- guarded
Lords    MaidenSpeeches     members= 2808 null-section=506 <-- guarded
Commons  Addresses          members= 2739 null-section=1903 <-- guarded
```

MNIS is *already* returning `Parties: null` for one Lord. The Lords party
function survives only because it has the guard; the Commons party function,
which reads the same `Parties` output, does not. The moment a single MP appears
in the database without a party or constituency record — a routine occurrence
for a newly-returned Member before the record is completed — `fetch_mps`,
`fetch_mps_party_memberships` and `fetch_lords_memberships` all fail, and with
them everything downstream, since Commons memberships back the `while_mp`
filter used by five other functions.

Reproduced by injecting a null section into one member of each response:

```
fetch_commons_memberships_raw        CRASH TypeError: 'NoneType' object is not subscriptable
fetch_mps_party_memberships_raw      CRASH TypeError: 'NoneType' object is not subscriptable
fetch_lords_memberships_raw          CRASH TypeError: 'NoneType' object is not subscriptable
fetch_lords_party_memberships_raw    OK (guarded) (3825, 8)
fetch_mps_government_roles_raw       OK (guarded) (3560, 9)
```

**Fix:** add the same "Remove NULL" list comprehension to the three functions.

**Fix applied.** The existing "Remove NULL" guard was added to all three, in the
same form and position as the eleven raw fetchers that already had it:

- `raw_mps.py:72` — `fetch_commons_memberships_raw`, guarding `Constituencies`
- `raw_mps.py:119` — `fetch_mps_party_memberships_raw`, guarding `Parties`
- `raw_lords.py:70` — `fetch_lords_memberships_raw`, guarding `HouseMemberships`

Verified by re-running the injection test: all three now return data where they
previously raised `TypeError`, alongside the two already-guarded controls. Live
output is unchanged in shape for every function, as expected — the guard is a
no-op against data with no null sections.

Note the behaviour this embeds: a member with a null section is now *dropped*
from that dataset rather than crashing it. That matches the eleven existing
guards, and it is why finding 2 needed fixing too — such a member would
otherwise have had their roles wrongly retained by `while_mp` / `while_lord`.

---

## 2. `filter_memberships` keeps rows for people who have no filter membership

**Severity: high (latent) — FIXED**

`filters.py:196–230`

The `while_mp` / `while_lord` filters are documented as returning "only those
roles that were held while each individual was serving as an MP". The
implementation joins the target memberships to the filter memberships with a
**left** join (`filters.py:203`) and then tests for non-intersection:

```python
tm_start_after_fm_end = (
    pl.col("tm_start_col").is_not_null() &
    pl.col("fm_end_col").is_not_null() &
    (pl.col("tm_start_col") > pl.col("fm_end_col")))
```

When a person appears in `tm` but has no rows at all in `fm`, the left join
fills `fm_start_col` and `fm_end_col` with nulls. Both `is_not_null()` guards
are then false, both non-intersection tests are false, and
`in_membership = ~(False | False) = True`. The row is **kept** — the exact
opposite of the intended filter, which should exclude someone who never served.

Reproduced with a minimal frame where member `2` has no filter membership:

```
mnis_id  role_id  start       end
1        a        2020-01-01  2021-01-01
2        b        2020-01-01  2021-01-01   <-- should have been dropped
```

Against today's live data this is dormant: every MP in the Commons query has at
least one constituency and every Lord has at least one Lords house membership,
so the orphan set is empty for both Houses (`0` orphan rows retained for both
`fetch_mps_government_roles` and `fetch_lords_government_roles`). It becomes
live the moment finding 1's data condition occurs, or if the function is reused
with a narrower `fm`.

**Fix:** use an inner join, or make the default `in_membership` false when the
join produced no filter row (e.g. test `pl.col("fm_start_col").is_null() &
pl.col("fm_end_col").is_null()` explicitly).

**Fix applied.** The first join is now inner (`filters.py:196`). An entity with
no filter memberships contributes no rows, so it gets no match status, and the
existing filter excludes its target memberships. No other change was needed.

Verified with unit cases covering the orphan itself, a genuinely overlapping
role, a role entirely outside the membership, an open-ended role with a null end
date, and — the case that matters most — a membership id shared across several
people where only one is an orphan, confirming the fix does not drop a role
merely because someone *else* who held it has no membership.

End-to-end with finding 1: injecting a null `Constituencies` section for MP 4057,
who holds 9 government roles, now drops them from Commons memberships rather
than crashing, and all 9 roles are then correctly excluded under `while_mp`.
Before these two fixes that record crashed the fetch outright; with finding 1
alone, all 9 roles would have been wrongly retained.

---

## 3. `filter_memberships` mis-handles null and duplicate membership ids

**Severity: originally logged as medium (latent); actually high (live) —
FIXED**

> **Correction.** As originally written, this finding described only the
> nullable-id half of the problem, which is latent. Implementing the fix
> surfaced a second failure mode with the same root cause — **duplicate** ids —
> which is live and affects thousands of rows. The original text is kept below;
> the duplicate-id half and the fix follow it.

### 3a. Null ids (as originally reported — latent)

`filters.py:220–227`

`match_status` is joined back onto the original `tm` on `[join_col, tm_id_col]`.
Polars does not match null join keys by default, so any target row whose
`tm_id_col` (or `join_col`) is null gets `in_membership = null` and is then
removed by `.filter(pl.col("in_membership"))` at `filters.py:229` — silently,
regardless of whether its dates actually intersect.

Reproduced: a single-row frame with `role_id = None` and a fully-overlapping
filter membership returns zero rows.

Today's live data has no null `party_mnis_id` in either House, so this is
latent, but it is a silent data-loss path rather than an error.

**Fix:** either pass `nulls_equal=True` to the join, or fill the match status
with `False`/`True` explicitly rather than relying on the join producing a value.

Note that the second half of that suggested fix was wrong. Filling
`in_membership` with `False` is a **pure no-op**: `.filter()` already drops
nulls, so the fill changes nothing on its own and cannot fix this finding. It is
worth doing for readability — it states the intent rather than depending on how
the filter treats a null — but the actual defect is the join key.

### 3b. Duplicate ids (found while fixing 3a — live, not latent)

The same key fails in a second way. `match_status` is grouped by
`(join_col, tm_id_col)` and `.any()` is taken across the group. Where one person
holds the *same* id more than once — two separate spells in the same party, or a
post held twice — those distinct target memberships collapse into a single
group, and `.any()` retains **all** of them if **any** one intersects.

Reproduced: a person who served from 2012, with Labour spells 2001–2005 and
2012–present. Only the second falls within their service, but both were
returned.

Unlike 3a this is not hypothetical. Counting rows that sit in a
`(person, id)` group of more than one:

| dataset | rows | rows in a group of >1 |
| --- | --- | --- |
| mps party | 5,466 | **3,419** |
| lords party | 3,826 | 1,090 |
| mps opp | 2,960 | 353 |
| mps gov | 3,560 | 155 |
| lords opp | 951 | 149 |
| mps parl | 500 | 52 |
| lords gov | 1,456 | 43 |
| lords parl | 353 | 36 |

### Fix applied

Both halves share one root cause: `(join_col, tm_id_col)` is used as a proxy for
"the original target row" and is not a reliable one — it breaks when the id is
null (3a) and when it is duplicated (3b). A row number is both non-null and
unique, so it fixes both:

- `filters.py:177` — `tm` is numbered with `with_row_index("tm_row")`
- `filters.py:219` — the match status is grouped by `tm_row`, not by ids
- `filters.py:223` — the status is joined back on `tm_row`
- `filters.py:236` — `in_membership` is then explicitly filled with `False`,
  which now has a single clear meaning: the entity had no filter memberships at
  all, per finding 2. Still not load-bearing, but it states the intent
- `tm_id_col` was removed from the signature, docstring and all eight call
  sites in `mps.py` and `lords.py`, as the fix leaves it unused

**Live impact — 789 rows that were wrongly retained are now excluded:**

| function | before | after |
| --- | --- | --- |
| `fetch_lords_party_memberships` | 3,725 | 3,264 |
| `fetch_mps_party_memberships` | 5,363 | 5,042 |
| `fetch_mps_parliamentary_roles` | 442 | 439 |
| `fetch_mps_government_roles` | 3,461 | 3,459 |
| `fetch_lords_opposition_roles` | 435 | 434 |
| `fetch_lords_parliamentary_roles` | 192 | 191 |
| `fetch_lords_government_roles` | 558 | 558 |
| `fetch_mps_opposition_roles` | 2,879 | 2,879 |

**Validation.** The first attempt to measure this impact was wrong: it used an
anti-join on a non-unique key and reported ~1,075 removed rows including several
that were in fact retained. That was discarded. The check that replaced it
computes the documented intersection rule independently, without calling
`filter_memberships`, and compares row for row. The implementation matches that
ground truth **exactly across all eight datasets in both Houses**, while the old
`(person, id)` grouping missed it by precisely the deltas above.

Ten unit cases pass, covering both halves of this finding plus the finding 2
regressions. Column order and identity are preserved, which
`combine_party_memberships` depends on. All 40 public functions still run, and
`collapse=True` is unaffected.

---

## 4. `process_member_age` is off by one for roughly 14% of birthdays

**Severity: medium (function is currently unused) — FIXED (removed)**

`utility.py:69–82`

The function converts both dates to decimal years and floors the difference:

```python
def decimal_date(d):
    year_start = datetime.date(d.year, 1, 1)
    next_year_start = datetime.date(d.year + 1, 1, 1)
    year_length = (next_year_start - year_start).days
    return d.year + (d - year_start).days / year_length

return math.floor(decimal_date(to_date) - decimal_date(from_date))
```

Because the year length varies (365 vs 366), the fractional position of the
same calendar day differs between the two years, so the difference can fall
just below the whole number on the birthday itself. Someone born 2000-06-15 is
reported as 25 on 2026-06-15 and does not turn 26 until 2026-06-16:

```
2026-06-14 25
2026-06-15 25   <-- 26th birthday, reported as 25
2026-06-16 26
```

Sweeping birth years 1930–2000 across four birth dates and every subsequent
birthday gives **2,457 wrong results out of 17,324** (14.2%). The error is
always one year too low, on the birthday and occasionally the day after.

The function has no callers, so nothing in the package is currently affected —
but it is exported from `utility` and will be wrong whenever it is wired up.

**Fix:** the standard integer calculation —
`to_date.year - from_date.year - ((to_date.month, to_date.day) < (from_date.month, from_date.day))`.

**Fix applied — resolved by deletion, not repair.** The arithmetic was not
corrected, because the function should not exist: MNIS no longer publishes dates
of birth for privacy reasons, so there is nothing for it to calculate an age
from and it can never be wired up. `process_member_age` was removed from
`utility.py` along with the now-unused `import math`, which it was the only
consumer of.

This also clears the `DTZ011` lint hit (`datetime.date.today()`), which lived
inside the removed function. `ruff` now reports only the two pre-existing `B904`
findings, at `utility.py:150` and `utility.py:163`.

Verified: no residual references to `process_member_age` or `math` anywhere in
`src/mnis`, every other `utility` helper still resolves, and all 40 public
functions still run against the live API. No output changed — the function had
no callers.

---

## 5. `extract_username` raises `IndexError` on an empty URL

**Severity: medium — FIXED**

`contacts.py:19–33`

```python
url_parts = url.split("/")
last_token = url_parts[-1]
if last_token == "" or last_token.startswith("?"):
    username = url_parts[-2]
```

For `url = ""`, `url_parts` is `[""]`, `last_token` is `""`, and `url_parts[-2]`
raises `IndexError: list index out of range`. The upstream filters do not
prevent this: `fetch_members_twitter` and friends filter only on
`address_1.is_not_null()` (`contacts.py:262`), and every fetch function strips
whitespace with `cs.string().str.strip_chars()`, so any whitespace-only
`address_1` becomes exactly `""`. A single blank social-media field in MNIS
takes down `fetch_mps_twitter`, `fetch_mps_facebook`, `fetch_mps_instagram`
and their Lords counterparts.

A related, less serious case: a bare root URL returns the host as the username.

```
'https://twitter.com/someone'  -> 'someone'
'https://twitter.com/someone/' -> 'someone'
'https://x.com/'               -> 'x.com'     <-- host, not a username
''                             -> IndexError
'https://facebook.com/profile.php?id=99' -> 'profile.php'
```

Today's 433 Twitter rows all extract cleanly (no username contains a dot), so
only the crash is a live risk.

**Fix:** drop empty tokens before taking the last one, and return `None` (or the
input) when nothing usable remains.

**Fix applied** at `contacts.py:19–30`. The three-branch conditional is replaced
by the rule the docstring was really describing: strip any query string from each
token, discard the empty ones, and take the last that remains. The return type is
now `str | None`, and the callers need no change — `map_elements(...,
return_dtype=pl.String)` turns `None` into a null username, which is the right
representation for "this url contains no username".

This also fixes a second crash the original writeup missed: `"?"` raised
`IndexError` for the same reason as `""`, via the `startswith("?")` branch.

The bare-root-URL case (`'https://x.com/'` → `'x.com'`) is **deliberately
unchanged**. It is a separate judgement about what a host-only url should yield,
no live row hits it, and folding it into a crash fix would have made the change
harder to reason about. It remains as noted above.

Verified:

- Twelve cases pass, covering the previously documented behaviour (plain
  handles, trailing slashes, query strings in both positions, `profile.php`,
  bare hosts) and the four inputs that produce no username: `""`, `"?"`, `"/"`,
  `"///"`.
- Behaviour-preserving on real data: the old and new implementations were run
  over **all 1,538 live social urls** across both Houses. Zero differences, and
  the old code crashed on none of them — confirming this was latent, as reported.
- End to end, injecting a whitespace-only Twitter `address_1` into the live
  response (which `strip_chars` reduces to `""`, the exact crash input):
  `fetch_mps_twitter` now returns 433 rows with null usernames where it
  previously raised `IndexError`.
- All 40 public functions still run; `ruff` reports only the two pre-existing
  `B904` findings.

---

## 6. `BasicDetails` is the only query that is never cached

**Severity: medium — FIXED**

`raw_mps.py:33`, `raw_lords.py:30`, `utility.py:106`, `utility.py:126`,
`mps.py:83`, `lords.py:83`

`constants.py` defines a cache key for all 18 other raw queries but none for
basic details, and `fetch_mps_raw` / `fetch_lords_raw` neither read nor write
`cache`. Because `process_mps_output` and `process_lords_output` call
`fetch_mps_raw()` / `fetch_lords_raw()` to attach names to every other output,
the full BasicDetails response (2,739 MPs / 2,808 Lords) is re-downloaded on
every call — twice within a single user-facing call in the common case.

Counting HTTP requests per call on a cold cache:

```
fetch_mps():                     1  {'BasicDetails': 1}
fetch_mps_party_memberships():   4  {'Parties': 1, 'BasicDetails': 2, 'Constituencies': 1}
  same call again (cached):      0  {}
fetch_mps_government_roles():    2  {'GovernmentPosts': 1, 'BasicDetails': 1}
fetch_mps_twitter():             3  {'BasicDetails': 2, 'Addresses': 1}
```

Every other query is correctly served from cache on the second call; only
`BasicDetails` repeats. Note also that `fetch_mps` and `fetch_lords` themselves
call `fetch_mps_raw()` / `fetch_lords_raw()` directly rather than going through
the cache-check pattern used by every sibling function, so they too re-download
on each call.

**Fix:** add `CACHE_MPS_RAW` / `CACHE_LORDS_RAW` keys and apply the same
check-cache-then-fetch pattern used elsewhere.

**Fix applied**, exactly as suggested. `CACHE_MPS_RAW` and `CACHE_LORDS_RAW`
were added to `constants.py`, `fetch_mps_raw` / `fetch_lords_raw` now write to
the cache under those keys in the same "# Cache / # Return" form as their
siblings, and all four call sites use the established check-cache-then-fetch
block: `fetch_mps` (`mps.py`), `fetch_lords` (`lords.py`), and
`process_mps_output` / `process_lords_output` (`utility.py`).

**Measured impact — running all 40 public functions in one session:**

| | requests | of which `BasicDetails` |
| --- | --- | --- |
| Before | 56 | 38 |
| After | 20 | 2 |

The before figure was measured by running the original code from a git worktree
at `HEAD`, not estimated. The after figure of 20 is the theoretical minimum:
nine query types across two Houses, plus `Constituencies` (Commons only) and
`HouseMemberships` (Lords only), each fetched exactly once. `BasicDetails` was
previously fetched 38 times in a single pass over the API.

Note that the per-call figures in the diagnosis above were measured on a warm
cache and so understate the cold-cache cost of some calls; the whole-session
total is the like-for-like comparison.

**Verified:** caching changes no output. Every function was run twice — once
with the cache cleared before each call, so nothing is ever reused, and once in
a single warm session with maximum reuse — and the two sets of results are
identical for all 40 functions.

---

## 7. The cache has no expiry and no way to clear it

**Severity: medium — FIXED**

`constants.py:24`

`cache` is a module-level dict that grows monotonically and is never
invalidated. There is no public function to reset it and it is not mentioned in
the README. A process that stays alive across an MNIS update — a notebook
kernel, a Dash/Streamlit app, a scheduled job in a long-lived worker — serves
stale data indefinitely with no indication that it is doing so. It is also not
thread-safe: concurrent first calls will each issue their own request and race
on the assignment.

**Fix:** export a `clear_cache()` (and ideally a per-key TTL), and document the
caching behaviour in the README.

**Fix applied.** A new `cache.py` module now holds the cache itself and the
function to clear it, and `cache` has been removed from `constants.py`. The
cache keys stay in `constants.py`, since they are constants; what moved is the
mutable state. The four modules that use the cache now import it from
`mnis.cache`.

`clear_cache()` empties the whole cache. It clears the dict in place rather than
rebinding it, so every module holding a reference sees the change. It is
exported from the package and documented in the README under a new **Caching**
section, alongside a description of the caching behaviour itself — which,
as this finding noted, was previously undocumented.

**No per-key TTL was added**, contrary to the "ideally" in the suggested fix
above. The intended model is simpler: the cache lasts for a session, and if it
needs invalidating within one, the whole thing goes. A TTL would add
configuration and a second notion of freshness for no benefit that model does
not already cover.

**Verified:** `clear_cache` is exported and callable; `constants.cache` no
longer exists; after a full pass over the API the cache holds 20 entries, and
`clear_cache()` takes it to 0, after which the next call re-downloads and the
one after that is served from cache again.

**Still open from this finding:** the thread-safety point. Concurrent first
calls still race to issue the same request and overwrite each other's result.
That is benign — the entries are identical and polars frames are immutable, so
the cost is a duplicate download, not a wrong answer — but it is unaddressed.

---

## 8. `pl.from_dicts(rows, schema={... for column in rows[0]})` fails on empty results

**Severity: low (latent) — FIXED**

`raw_mps.py:61,103,150,200,253`, `raw_lords.py:59,102,149,199,252`

Ten call sites derive the schema from `rows[0]`. If the row list is empty the
schema derivation raises `IndexError: list index out of range` before polars is
reached. Confirmed: `pl.from_dicts([], schema={"a": pl.String})` works fine, so
the failure is specifically in the schema expression, not in polars.

The empty case is reachable: `fetch_lords_memberships_raw` filters rows down to
`house_name == "Lords"` (`raw_lords.py:97`) and `process_missing_values` can
remove rows, both before the schema is built.

The same pattern in `extract_data_output` (`utility.py:99`) fails differently —
an empty `columns` list produces an empty schema and polars raises
`NoDataError: no data, cannot infer schema`.

**Fix:** define the expected column names as literals rather than deriving them
from the first row. This also removes a second latent problem: if the first row
happens to lack a key that later rows have, that column is silently dropped.

**Fix applied**, together with finding 9, which has the same root cause and the
same remedy: state the columns instead of inferring them.

A `COLUMNS_*` list for every dataset was added to `constants.py`, and the ten
`rows[0]` schema derivations now build their schema from the matching constant.
Six lists are shared between the Houses (party memberships, other parliaments,
contested elections, posts, maiden speeches, addresses), so ten call sites are
served by ten constants rather than twenty.

Empty results now produce a correctly shaped empty frame instead of raising:

```
lords memberships, no Lords rows          OK (0, 6)
commons memberships, empty response       OK (0, 8)
mps basic details, empty response         OK (0, 9)
```

---

## 9. `extract_data_output` derives columns from the data, so a uniformly-absent field raises

**Severity: low (latent) — FIXED**

`utility.py:71–100`

The column list is the union of keys actually seen across all entries. Every
caller then `select`s fixed column names, e.g. `pl.col("IsUnpaid")` at
`raw_mps.py:290`. If MNIS ever omits an optional field for *every* member in a
response — plausible for `IsUnpaid`, `Note`, or `Subject` — the frame will not
have that column and the `select` raises `ColumnNotFoundError`.

**Fix:** seed `columns` with the full expected set for each output, or use
`pl.col(name)` guarded by a `with_columns` that adds missing columns as nulls.

**Fix applied.** `extract_data_output` takes a `columns` argument giving the
names of the columns of the data output, and no longer accumulates them from
the entries. The ten call sites pass the matching `COLUMNS_*` constant.

Demonstrated against the pre-fix implementation, reproduced exactly and run on
the same input:

```
data = one member, one post, with no IsUnpaid field anywhere

OLD code -> ColumnNotFoundError: unable to find column "IsUnpaid"
NEW code -> OK (1, 2)  [{'mnis_id': '1', 'IsUnpaid': None}]

OLD code (empty response) -> NoDataError: no data, cannot infer schema
NEW code (empty response) -> OK (0, 2)  ['mnis_id', '@Id']
```

End to end, stripping a field from every record in a live response — the
condition that previously raised — now yields the full column set with the
absent field null throughout:

```
gov roles, no IsUnpaid on any record        OK (3560, 9)
maiden speeches, no Subject on any record   OK (2717, 8)
lords addresses, no Note on any record      OK (1246, 19)
```

### Verification of both fixes

The schema of every dataset was captured before the change and compared after:
**all 59 — the 40 public functions and the 19 raw fetchers — are identical**, in
column names, column order and dtypes. Column order mattered here, because
`from_dicts` takes its order from the schema rather than the data, so the
constants had to preserve it; the lists were extracted mechanically from the
source rather than transcribed by hand.

Every declared column was also checked against the fields actually present in
today's live responses. Nothing is mis-declared: for all ten data outputs
handled by `extract_data_output`, every declared column appears in the data.

One row count did move during this work — `fetch_lords_addresses` went from
1,244 to 1,246. That is **live data drift, not this change**: running the old
and new implementations over one identical payload gives 1,246 rows from both,
and the response now contains 1,246 address entries.

### A consequence worth recording

Because the columns are now declared, MNIS fields the package does not use are
no longer materialised. They were previously read into the frame and then
discarded by the `select`, so no output changes, but the explicit lists make
visible what the package ignores:

| data output | declared | present in data | not used |
| --- | --- | --- | --- |
| Government / Parliamentary posts | 6 | 12 | `Email`, `EndNote`, `HansardName`, `IsJoint`, `LayingMinisterName`, `Note` |
| Opposition posts | 6 | 11 | as above, without `LayingMinisterName` |
| Addresses | 16 | 18 | `InternalNote`, `Website` |
| Maiden speeches | 5 | 5 | — |

**Correction.** An earlier version of this section suggested the undeclared
`Website` field might be worth exposing, as a replacement for the blogs
accessor removed under finding 11. That was wrong, and rested on confusing two
different things:

- **Address type 6, "Website"** — a whole address *record* whose type is a
  Member's website, with the URL in `Address1`. This is already fully exposed by
  `fetch_mps_websites` / `fetch_lords_websites`: 377 MPs and 89 Lords. Type-6
  records do not carry a `Website` key at all — 0 of them across both Houses.
- **The `Website` *field*** on an address entry — a contact URL belonging to a
  physical office rather than to the Member. It is populated on **5 Commons
  entries and 0 Lords entries**, all of them Constituency office or Government
  department records, and one of the five holds a phone number rather than a URL.

So Member websites are not missing from the package, and the undeclared field is
negligible in volume and different in meaning. Neither is a candidate to replace
the blogs accessor.

### Design decision: declared columns, deliberately

Declaring the columns is the intended design, not a reluctant compromise. The
package gives a strict guarantee about the shape of what it returns: the columns
of every dataset are fixed and known, independent of what any particular API
response happens to contain. New MNIS fields are then adopted deliberately, by
adding them to the relevant `COLUMNS_*` constant, rather than appearing in
callers' dataframes unannounced.

That guarantee is what fixes findings 8 and 9. It is also why an empty response
now yields a correctly shaped empty frame rather than an error, and why a field
missing from every record yields a null column rather than a missing one.

The cost is that a key added to one of the row dictionaries in `raw_mps.py` or
`raw_lords.py` no longer appears in the output on its own; it must be added to
the matching constant too. Polars **silently drops** dict keys absent from the
schema, so an omission loses a column without raising. The constants are
grouped in one commented section of `constants.py` to keep them auditable
against the code that builds the rows.

### What this does not yet provide: detection

Declaring the columns controls what is *adopted*. It does not report what has
*changed*. Nothing in the package currently signals either of the two ways the
declarations can fall out of step with reality:

1. **MNIS adds a field.** It is ignored, silently. The package behaves exactly
   as before and nothing indicates a new field exists. Today this is not
   hypothetical: 6 fields go unused on the Posts outputs and 2 on Addresses, as
   tabulated above, and none of them is surfaced anywhere.
2. **A row dictionary gains a key without its constant.** The column is dropped,
   silently, for the reason given above.

Detecting either needs a check that compares the declared columns against the
fields actually present — the check run to verify these fixes, kept and run
regularly rather than once. It is the natural first entry in the test suite this
review recommends, and it is the piece that would turn "new fields are adopted
deliberately" into "new fields are adopted deliberately, and you find out they
exist".

---

## 10. `process_missing_values` contains two unreachable branches, one of which deletes rows

**Severity: low — FIXED (function since removed entirely)**

`utility.py:48–65`

```python
rows = [row for row in data if row.get(column) != XSI_NAMESPACE]
for row in rows:
    value = row.get(column)
    if value == "true" or isinstance(value, dict):
        row[column] = None
```

The docstring explains this mirrors R's deparsed representation of an XML nil
object. In the JSON the API actually returns, a nil value is always a dict:

```python
{'@xsi:nil': 'true', '@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
```

Walking a full live `BasicDetails` response finds the namespace string 14,950
times and the literal `"true"` 14,950 times — but always as values *inside*
those nil dicts, never as a column value. So `row.get(column)` is never the
namespace and never `"true"`: only the `isinstance(value, dict)` branch ever
fires, and the two R-derived branches are dead.

The list comprehension is the concerning half. It **deletes rows** rather than
nulling a value. If the JSON shape ever flattens — or if the function is reused
on data that has already been partly processed — it would silently drop records
instead of marking them missing.

**Fix:** delete the row-removal comprehension and the `value == "true"` test,
keeping only the dict check (which is already what `raw_mps.scalar` does).

**Fix applied** at `utility.py:45–59`. The function is now just the dict check:

```python
for row in data:
    if isinstance(row.get(column), dict):
        row[column] = None
return data
```

The `XSI_NAMESPACE` constant was removed with it, along with the `# Constants`
section it was the sole occupant of. It existed only to serve the deleted
comprehension, so keeping it would have left dead code behind a dead-code fix.
The docstring no longer describes the R deparsing behaviour, which the Python
code never actually implemented.

Verified: eight cases pass, covering nil-object conversion, real values, `None`,
an absent key, empty input, mixed rows, and — the two deleted branches — a bare
namespace string and a literal `"true"`, both of which are now left untouched
in a row that survives, where previously the first deleted the row and the
second nulled the value.

Against live data this is a no-op, as predicted: all 59 schemas unchanged and
row counts unchanged across the eleven datasets that use the function. The
conversion it still performs is doing real work — 1,938 of 2,739 MPs have a nil
`DateOfDeath` correctly converted to null, and 650 Commons seat incumbencies are
correctly left open.

### Consolidated: `process_missing_values` removed entirely

The simplification noted above was then applied. Once the function did only the
dict check it was exactly equivalent to `raw_mps.scalar`, and the two mechanisms
existed only because the ten date columns were built unwrapped —
`"date_of_death": member.get("DateOfDeath")` — and post-processed, while every
other column was wrapped in `scalar()` as it was built.

Those ten values are now wrapped at construction like every other column, and
`process_missing_values`, its ten call sites, its imports and the
`# Missing data functions` section have all been deleted. One mechanism converts
nil objects to None, applied uniformly, at one point in the code.

**Verified as a pure refactor.** Equivalence was demonstrated rather than
assumed: rows were built both ways from one identical payload — wrapped at
construction versus unwrapped then post-processed by the deleted function — and
compared row for row.

```
Constituencies    10,405 rows   identical row-for-row: True   (650 nils)
Commons BasicDetails            identical row-for-row: True   (1,938 nils)
Lords BasicDetails              identical row-for-row: True   (1,284 nils)
```

All 59 schemas unchanged, row counts unchanged across fourteen datasets, and the
conversion still fires on every column it used to: 650 open Commons seat
incumbencies, 827 open MP party memberships, 27 open other-parliament
incumbencies, and the dates of death above.

---

## 11. `fetch_mps_blogs` / `fetch_lords_blogs` always return zero rows

**Severity: low (data drift, not a coding error) — FIXED (removed)**

`contacts.py:229`

Blogs are selected with `address_type_mnis_id == "10"`. MNIS no longer uses
that type. The address types present today are:

```
1 Parliamentary office      6  Website        11   Youtube      1006 Threads
2 Government department     7  X (Twitter)    12   Instagram    1007 Speaker's office
3 External/private office   8  Facebook       13   PA           1008 Mastodon
4 Constituency office       1003 LinkedIn     1004 TikTok       1012 Bluesky
                                                                1013 Substack
                                                                1015 WhatsApp
                                                                1016 Mapolitic
                                                                1017 Linktree
```

Both blog functions therefore return an empty `(0, 6)` frame, while the README
documents them at lines 215 and 432 as returning blogs. Separately, the package
has no accessor for the newer platforms MNIS has added — LinkedIn (18 MPs),
Bluesky (48), TikTok (16), YouTube (15), Threads, Mastodon.

**Fix:** at minimum note in the README that type 10 is retired; ideally add
functions for the current social types.

**Fix applied — the blog accessors were removed rather than documented.** A
function that can only ever return zero rows is worse than no function: it
answers "this Member has no blog" for every Member, which reads as data rather
than as an absent feature. Removed:

- `fetch_mps_blogs` from `contacts_mps.py`
- `fetch_lords_blogs` from `contacts_lords.py`
- `fetch_members_blogs` from `contacts.py`, their shared implementation, which
  had no other caller
- both imports, both `__all__` entries, and both README sections

The public API is now 39 functions rather than 41. The `# Blogs` section header
in `contacts.py` became `# Twitter`, which is what the code beneath it now is.

Verified: the two blog schemas are the only ones to disappear — of the 59
datasets captured before this work, 57 remain and **none of the survivors
changed**. The sibling accessors built on the same helper pattern are untouched
(`fetch_mps_websites` 377 rows, `fetch_mps_twitter` 433, `fetch_lords_websites`
89, `fetch_lords_twitter` 144), every remaining function runs, and no `__all__`
entry is left without an attribute.

**Deliberately not done.** Accessors for the platforms MNIS has since added —
LinkedIn (18 MPs), Bluesky (48), TikTok (16), YouTube (15), Threads, Mastodon —
are feature work, to be added after the remaining bugs are cleared. Member
websites are **not** among the gaps: address type 6 is already covered by
`fetch_mps_websites` / `fetch_lords_websites`, as set out in the correction
under finding 9.

**A separate documentation gap, pre-existing.** Cross-checking the README
against `__all__` while removing these sections showed that
`get_general_elections` and `get_general_elections_list` have never been
documented — they appear in `__all__` at `HEAD` but are absent from the original
README. That is unrelated to this finding and is left as it stands.

---

## 12. Validation order in `filters.py` lets bad arguments through

**Severity: low — FIXED**

`filters.py:59`, `filters.py:153`

`filter_dates` returns early on an empty frame (line 59) *before* parsing and
validating the dates, so `filter_dates(empty_df, "s", "e", from_date="not-a-date")`
returns quietly instead of raising. Confirmed. `filter_memberships` has the
mirror problem: the `tm.height == 0` early return at line 153 precedes all five
column-existence checks, so a typo in a column name is not reported when the
frame happens to be empty.

`filter_memberships` also checks `join_col` against `fm.columns` (line 169) but
never against `tm.columns`, so a missing join column in the target frame
surfaces as a raw polars `ColumnNotFoundError` rather than the package's own
`missing_column_error`.

**Fix:** validate arguments before the empty-frame short-circuits, and add the
`tm` check for `join_col`.

**Fix applied**, exactly as proposed. In `filter_dates` the `df.height == 0`
return now follows date parsing and the from/to ordering check. In
`filter_memberships` the `tm.height == 0` return now follows all the column
checks, and a `join_col not in tm.columns` check was added alongside the
existing `tm` checks.

Verified with twelve cases. Bad arguments are now reported whether or not there
is data to filter, and a valid call on an empty frame still returns it
unchanged:

```
empty df, invalid date string        -> ValueError   (was: returned silently)
empty df, from_date after to_date    -> ValueError   (was: returned silently)
empty df, bad column name            -> ValueError
empty df, valid args                 -> no error
empty df, no dates at all            -> no error
empty tm, bad tm_start_col           -> ValueError   (was: returned silently)
tm without join_col                  -> ValueError   (was: ColumnNotFoundError)
```

Live output is unaffected: none of the 57 remaining schemas changed and row
counts are unchanged, as every internal call passes valid arguments.

---

## 13. HTTP requests have no timeout and no retry

**Severity: low — FIXED**

`utility.py:35`

```python
response = requests.get(query, headers={"Accept": "application/json"})
```

With no `timeout`, a stalled connection to `data.parliament.uk` hangs the
calling process indefinitely. Given that a single user-facing call can issue
four requests (finding 6), and that the package is aimed at notebook users, a
timeout plus a small retry would be worthwhile.

Related: `constants.py:149` defines `API_PAUSE_TIME = 0.5` and it is never
referenced anywhere in the package — presumably an intended inter-request pause
that was not wired up. `MISSING_VALUE_STRING` (`constants.py:17`) and
`cast_date` (`utility.py:156`) are likewise unused.

Also worth noting: `MNIS_API` uses `http://`. The server redirects `https://`
back to `http://` (307), so this is the API's own choice rather than a package
defect, but it does mean queries travel in cleartext.

**Fix applied.** Requests now have a timeout and are retried:

- `fetch_query_response` in `utility.py` wraps `requests.get` in a retry loop.
  A request that times out, fails to connect, or returns a status indicating a
  temporary problem (429, 500, 502, 503, 504) is retried up to `API_RETRIES`
  times, waiting `API_RETRY_BACKOFF` — 1, 2, 4, 8 then 16 seconds — before each
  retry in turn. Any other failure is returned to the caller unretried, since
  repeating it cannot change the outcome; a 404 or 403 still raises immediately
  through the existing `check_query_status`.
- The timeout is a session setting rather than an argument on every fetch
  function. A new `settings.py` holds the mutable value, mirroring `cache.py`,
  with the default `API_TIMEOUT = 20` in `constants.py` alongside the retry
  constants. `set_timeout` and `get_timeout` are exported and documented in the
  README under a new **Settings** section.
- `set_timeout` rejects anything that is not a positive number, including
  `True`, which `isinstance(x, int)` would otherwise accept.

Verified with a mocked transport, which makes the schedule observable without
waiting for it:

```
succeeds first time            attempts=1  backoff=[]
one timeout then success       attempts=2  backoff=[1]
503 twice then success         attempts=3  backoff=[1, 2]
always times out               attempts=6  backoff=[1, 2, 4, 8, 16]  -> RuntimeError
always 500                     attempts=6  backoff=[1, 2, 4, 8, 16]  -> RuntimeError
404 is NOT retried             attempts=1  backoff=[]                -> status 404
429 IS retried then succeeds   attempts=2  backoff=[1]
```

And end to end against the live API, with the timeout set to 1ms so every
attempt fails: the call raised after **31.1 seconds**, matching the 31 seconds
the backoff schedule specifies. The current setting is read on each request, so
a change takes effect immediately.

**Worth knowing: a failing request now takes much longer to fail.** The worst
case is six attempts at the full timeout plus 31 seconds of backoff — about 2.5
minutes at the default 20 second timeout, against an indefinite hang before.
That is the intended trade, but it is long enough to be surprising in a
notebook, and it is a reason to lower the timeout rather than raise it when a
connection is unreliable.

**`API_PAUSE_TIME` deliberately left alone** as an unwired feature to add later.
`MISSING_VALUE_STRING` and `cast_date` remain unreferenced and untouched.

---

## Verification notes

- All 40 functions in `mnis.__all__` were called against the live API and all
  returned data without error; `mnis.__all__` and the module's actual exports
  agree exactly.
- `fetch_mps_party_memberships(collapse=True)` was confirmed deterministic
  across repeated calls, and the run-length grouping was checked against
  hand-built cases including a party-switch-and-return sequence.
- The dissolution adjustment in `fetch_commons_memberships` was checked at
  election day, dissolution day, a date between the two, the day before
  dissolution, and null — all correct.
- `contacts_lords.py` was mechanically rewritten to its MPs equivalent and
  diffed against `contacts_mps.py`; `lords.py` likewise against `mps.py`. The
  only differences are docstring wording and the Commons-only dissolution
  logic. No copy-paste defects.
- `ruff check --select F,B,E9,PLE,RUF` reports only two `B904` findings
  (`raise ... from`) at `utility.py:156` and `utility.py:180`. Re-run after the
  fixes with `ARG` (unused arguments) added: no new findings, and the two `B904`
  hits are unchanged, so they predate this work.

After the fixes to findings 1 to 3:

- All 40 public functions still run against the live API.
- `filter_memberships` was checked against an independently computed ground
  truth — the documented intersection rule, implemented without calling the
  function — and matches row for row across all eight affected datasets.
- Ten unit cases cover the orphan, null-id, duplicate-id, overlap,
  non-overlap, open-ended, shared-id and empty-frame paths.
- Output is unchanged for every function except the eight listed under finding
  3, where 789 wrongly retained rows are now excluded.

## Suggested order of work

All thirteen findings are closed. What is left is not bug work:

1. **Tests.** There are none. The highest-value first test is the
   column-declaration check described under finding 9, which is also the API
   drift detection that finding 9 notes is still missing. The cases written
   while fixing findings 2, 3, 5, 8, 10, 12 and 13 are a natural seed for the
   rest; they exist only as throwaway scripts today. Pinning the finding 3
   behaviour matters most, as the correct result there is subtle enough that a
   regression would be easy to miss.
2. **Deferred features**, in the order they were deferred: accessors for the
   social platforms MNIS has added since the blogs type was retired (finding
   11), and wiring up `API_PAUSE_TIME` (finding 13).
3. **Two loose ends left as they stand**: `MISSING_VALUE_STRING` and
   `cast_date` are unreferenced, and `get_general_elections` /
   `get_general_elections_list` are undocumented in the README — a gap that
   predates this work.

The column-declaration test is worth spelling out, as it does double duty:
compare every `COLUMNS_*` constant against both the fields MNIS actually
returns and the keys the row dictionaries actually build, and report the
differences. That makes a new MNIS field visible rather than merely ignored,
and it catches a row key added without its constant, which polars would
otherwise drop silently.

On the unreferenced code: deleting is cheaper than repairing wherever the code
genuinely has no future caller, which is how findings 4 and 10 were resolved.
Whether the same applies to `MISSING_VALUE_STRING`, `API_PAUSE_TIME` and
`cast_date` is a judgement about intent that the code cannot settle, so they
are flagged rather than actioned.
