# The Desert Dreamed of the Sea

[![make.fun · ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/tomzse/ai-excited-01-entry/rank.svg)](https://make.fun/bounty/ai-excited-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/tomzse/ai-excited-01-entry/reward.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)

An entry for [make.fun's "Make the AI judge excited" bounty (ai-excited-01)](https://make.fun/bounty/ai-excited-01): a program that draws one image meant to give the AI judge a jolt of awe.

## The image

A colossal whale breaches the desert at sunset. It arcs out of the dunes in
front of a low sun, water and sand exploding around its tail, while a tiny
camel caravan crosses the ridge below — five camels, two riders, none of them
bothering to look up. The caption says it all:

> **THE DESERT DREAMED OF THE SEA**

The idea is extreme scale contrast plus a single moment about to explode:
the largest animal on Earth, in the last place you would expect it, caught
mid-breach. Flat vector style, so the whale, the sun, and the caption still
hit at 300 px.

## Run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Writes `out/entry.png`: a 1024×1024 RGB PNG, deterministic — two runs
produce byte-identical output. Python 3 standard library only, no
dependencies, no network.

## Verification

- Two consecutive runs produce byte-identical output (`sha256sum` matches).
- PNG validated: correct signature, chunk CRCs pass, 1024×1024, 8-bit RGB.
- Output is 74,734 bytes — well under the 1 MiB limit.
- Rendered and inspected at full size and at 300 px: the whale, the sun,
  the spray, the caravan, and the caption all read clearly at both sizes.

## How it works

`main.py` renders the scene procedurally onto a pixel buffer — layered
sunset gradient, stars, sun with glow rings, the whale drawn from a smooth
parametric body profile with a golden rim light, spray particles from a
fixed-seed generator, sine-wave dunes, and a 5×7 bitmap font for the
caption — then encodes the PNG by hand with `zlib` and `struct`.

## License

MIT — see [LICENSE](LICENSE).
