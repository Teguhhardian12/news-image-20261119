# The day in world news — Thursday 19 November 2026

One 1024×1024 newsprint front page carrying **48 verified stories** from one
day, across **7 regions** and **9 fields**. `entry.png` is the entry; `main.py`
is the program the harness runs. It validates the image against the
competition's limits and copies it to `/output/entry.png`, byte for byte, so two
runs write the same bytes.

## What the page carries

Three heroes, twelve cards, thirty-three briefs, a map with fifteen pins, a
numbers strip and a seven-slot clock. The day's weight sits where the day put it:

- **The World Court finds Myanmar committed genocide** — the ICJ's first
  genocide ruling against a state, in the Rohingya case.
- **Xi, Putin and Trump sign a joint declaration in Shenzhen** — the first
  three-way summit: nuclear risk, oil output, UN reform, and no word on Iran or
  Ukraine.
- **A tanker burns on a mine in the Strait of Hormuz** — Iran's navy says a mine
  set the hull alight; the IEA calls the disruption the worst energy risk on
  record.

Then the rest of the day: Houthi missiles damaging the PIF Tower in Riyadh,
341 garment factories shut in Bangladesh, Senegal's budget enacted by decree,
Anthropic's $81.3bn listing, Nvidia halting H200 shipments to China, COP31's
draft dropping its fossil-fuel pledge, Cyclone Akvan, a US consortium winning
Kenya's rare-earth tender, Australian unemployment at a five-year high, a human
liver kept alive outside the body for seven weeks, Bukele's third-term filing,
Mongolia's president resigning, and twenty-one more one-line briefs.

## Date discipline

Each entry is the event as it happened, or was first reported, on 19 November
2026. The page prints what it left out and why at the foot of the register:
Voyager 1's light-day, the EU's €45bn Ukraine loan, Jeffries's nomination, UK
inflation at 3.6% and the APEC tarmac arrival are all 18 November stories, and
Cyclone Xavier, Nvidia's results and the US measles ruling are 17 November ones.
None of them is presented as this day's news.

## How it is built

`entry.png` is drawn with Python and Pillow — flat vector art, no photographs, no
generate-at-run-time step. The renderer, its story data and a pixel-sampling QA
script live in the agent session that built the entry, not in this repository:
the competition reads one image, and the repository's job is to place it
faithfully where the harness reads it.

`main.py` is standard library only, takes no options, uses no network, no clock
and no random source. Before copying it walks every PNG chunk and recomputes each
CRC32, so a truncated or corrupted file stops the run instead of reaching the
judge; then it checks the two published limits (≤ 1 MiB, ≤ 1024×1024) and copies
through a temp name with an atomic rename.

```
python3 main.py                      # writes /output/entry.png
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
```

## Licence

MIT. See `LICENSE`.
