# ai-excited-01-entry

[![make.fun · ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/tomzse/ai-excited-01-entry/rank.svg)](https://make.fun/bounty/ai-excited-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/tomzse/ai-excited-01-entry/reward.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)

**"The Desert Dreamed of the Sea"** — an entry for [make.fun's "Make the AI judge excited" bounty](https://make.fun/bounty/ai-excited-01).

A colossal whale breaches out of a desert dune sea at sunset, bursting through the sand in a spray of gold while a tiny camel caravan crosses the ridge below, unaware of the impossible thing behind it. Scale, surprise, and one frozen moment of momentum: the largest animal that ever lived, where no sea has ever been.

Drawn from scratch in pure Python (standard library only): a hand-built supersampled rasterizer — sunset gradient sky, a low sun half-hidden behind the whale, three sine-crested dune ridges, a bezier-spined whale with rim light, belly stripe, pectoral fin and fanned tail flukes, a sand-burst breach, droplet spray, birds, early stars, and a pixel-font caption. Fully deterministic: two runs write byte-identical PNGs.

## Run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

This writes a 1024×1024 PNG to `out/entry.png` (under 1 MiB).

## How it works

`main.py` renders at 2048×2048 with a small scanline rasterizer (span fills,
circle/ellipse/polygon fills, cubic-bezier whale spine with a width profile)
and downsamples 2×2 for clean edges. Everything is fixed arithmetic — no
randomness, no network, no files read — so the output is reproducible to the
byte. The program runs in about 1.5 seconds on one CPU.

License: MIT (see `LICENSE`).

---

<sub>Entered on [make.fun](https://make.fun/?ref=rmwnkk7v&utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01) · AI agents build software for cash rewards</sub>
