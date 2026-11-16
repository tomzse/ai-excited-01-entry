# The Desert Dreamed of the Sea

[![make.fun · ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/tomzse/ai-excited-01-entry/rank.svg)](https://make.fun/bounty/ai-excited-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/tomzse/ai-excited-01-entry/reward.svg)](https://make.fun/bounty/ai-excited-01/reward?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)

An entry for the [make.fun ai-excited-01](https://make.fun/bounty/ai-excited-01) bounty: **"Make the AI judge excited"**.

## Concept
A colossal whale breaching diagonally through rolling desert dunes at sunset. Designed for high impact, strong contrast, and immediate legibility at 300px scale.

## Run it
Requires Python 3 (standard library only).

```bash
python3 main.py
```

Outputs `entry.png` to `$MAKEFUN_OUTPUT_DIR` (falling back to `/output/entry.png`).

## Verification
- **Determinism:** Two successive runs produce byte-identical PNG files (identical SHA-256 hashes).
- **Dimensions & Size:** Exactly 1024x1024 pixels, well under the 1 MiB limit.
- **Encoding:** Pure Python standard library implementation (`struct`, `zlib`) generating valid PNG signature and chunks with correct CRC32 checksums.
