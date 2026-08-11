# Destiny Data Compendium mirror

This directory holds a local CSV mirror of the community-maintained **Destiny Data
Compendium** spreadsheet — the most current reference for weapon/armor/artifact perk
behavior, subclass verbs (Arc/Solar/Void/Stasis/Strand/Prismatic), exotics, and game
mechanics. Trust it over model memory and over most wikis.

Source: <https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4>

## Rebuilding the mirror

The CSVs are **gitignored** — the data belongs to the Compendium's authors and goes
stale with every patch, so we keep the fetcher in git, not the snapshot:

```
./venv/Scripts/python.exe fetch_compendium.py          # current tabs
./venv/Scripts/python.exe fetch_compendium.py --all    # + OLD archive tabs
```

`_meta.json` records when the mirror was last fetched and which tabs/gids it holds.
**Check that date before leaning on the data** — if it predates the current season,
re-run the fetch.

## Reading the CSVs

- One file per sheet tab (`weapon-perks.csv`, `prismatic.csv`, …).
- **Grep gotcha:** these CSVs are gitignored, and ripgrep skips gitignored files —
  a directory-wide `rg`/Grep over `research/` will silently miss the mirror. Search
  a CSV by its explicit file path, or use `rg --no-ignore`.
- The sheet uses merged cells and blank spacing heavily; the fetcher drops empty
  rows/columns but header rows can still repeat mid-file where the sheet had section
  banners. Grep for the perk/mod name rather than assuming clean tabular structure.
- Perk descriptions include the Compendium's tested numbers (buff percentages,
  timers, caveats) — this is exactly the detail that belongs in citations for
  `research/god-rolls.md` and `DESTINY_REFERENCE.md`.

## Relationship to the rest of the repo

- `research/god-rolls.md` stays the authoritative per-weapon verdict doc; the
  Compendium is a *source* for it, not a replacement.
- `rules.yaml` perk names must match **in-game text** exactly — the Compendium
  usually matches in-game spelling, but verify against a scan before adding rules
  from it.
