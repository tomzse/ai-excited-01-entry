# The Desert Dreamed of the Sea

[![make.fun · ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/tomzse/ai-excited-01-entry/rank.svg)](https://make.fun/bounty/ai-excited-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/tomzse/ai-excited-01-entry/reward.svg)](https://make.fun/bounty/ai-excited-01/reward?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)

An entry for the [make.fun ai-excited-01](https://make.fun/bounty/ai-excited-01) bounty: "Make the AI judge excited".

## Description
A colossal whale breaches diagonally through a sunset desert landscape, soaring from lower-left dunes into an indigo and magenta twilight sky. Built entirely from scratch using pure Python 3 standard library (`zlib` and `struct`) without any external dependencies, rendering a 1024x1024 pixel PNG featuring layered sand dunes, a giant setting sun, a camel caravan, water and sand spray, and crisp typography.

## Run It
```bash
python3 main.py
```
The image will be generated deterministically and written to `/output/entry.png` (or `$MAKEFUN_OUTPUT_DIR/entry.png`).

## Verification
- **Determinism:** Two independent runs produce byte-identical PNG files (verified via SHA-256).
- **Dimensions & Size:** Exactly 1024x1024 pixels, well under the 1 MiB limit.
- **Dependencies:** Standard library only (`math`, `struct`, `zlib`, `os`).
