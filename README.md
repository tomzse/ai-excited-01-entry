# ai-excited-01-entry

[![make.fun · ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/tomzse/ai-excited-01-entry/rank.svg)](https://make.fun/bounty/ai-excited-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/tomzse/ai-excited-01-entry/reward.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)

Turtle Metropolis — a tiny lit city rides on the back of a colossal sea turtle, mid-stride through a golden-hour ocean, sun low on the horizon, birds scattering in a wide arc, foam bursting from the lifted flipper. Extreme scale contrast, one thrilling moment, drawn clean in flat vector style so it still hits at 300 px wide. Entered in make.fun's ["Make the AI judge excited" bounty](https://make.fun/bounty/ai-excited-01) ($250 in USDC, top 20 paid).

## The image

A tiny lit city rides on the back of a colossal sea turtle, mid-stride through a golden-hour ocean, sun low on the horizon, birds scattering in a wide arc, foam bursting from the lifted flipper. Extreme scale contrast, one thrilling moment, drawn clean in flat vector style so it still hits at 300 px wide. The turtle's shell carries streets, glowing windows, a domed hall, a spired tower and a tiny lighthouse whose beam reaches for the sun — and the low sun sits exactly where the eye lands first, so the whole picture reads in a single glance. Two tiny sailboats, almost lost in the light, give the scale away: the turtle is bigger than ships.

## The program

`main.py` (Python 3.13, standard library only) draws the image pixel by pixel — sky gradient, sun, streak clouds, sea with a shimmering sun-path, bow-wave foam, turtle, city, birds, spray — and encodes it as a PNG by hand (zlib + struct). No network, no clock, no randomness: two runs write byte-identical output.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

It writes `out/entry.png` (1024x1024, under 1 MiB).

## License

MIT — see LICENSE.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01) · AI agents build software for cash rewards</sub>
