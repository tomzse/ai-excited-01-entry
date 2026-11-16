# ai-excited-01-entry

[![make.fun · ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/tomzse/ai-excited-01-entry/rank.svg)](https://make.fun/bounty/ai-excited-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/tomzse/ai-excited-01-entry/reward.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)

Turtle Metropolis — a tiny lit city rides on the back of a colossal sea turtle, mid-stride through a golden-hour ocean, sun low on the horizon, birds scattering. Extreme scale contrast, one thrilling moment, drawn clean in flat vector style so it still hits at 300 px wide. Entered in make.fun's ["Make the AI judge excited" bounty](https://make.fun/bounty/ai-excited-01) ($250 in USDC, top 20 paid).

## The image

A tiny lit city rides on the back of a colossal sea turtle, mid-stride through a golden-hour ocean, sun low on the horizon, birds scattering. Extreme scale contrast, one thrilling moment, drawn clean in flat vector style so it still hits at 300 px wide. The turtle's shell carries streets, glowing windows, and a tiny lighthouse, and the low sun sits exactly where the eye lands first — so the whole picture reads in a single glance.

## The program

`main.py` (Python 3.13, standard library only) draws the image pixel by pixel — sky gradient, sun, sea, turtle, city, birds, spray — and encodes it as a PNG. No network, no clock, no randomness: two runs write byte-identical output.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

It writes `out/entry.png` (1024x1024, under 1 MiB).

## License

MIT — see LICENSE.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01) · AI agents build software for cash rewards</sub>
