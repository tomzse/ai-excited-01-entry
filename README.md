# ai-excited-01-entry

Make the AI judge excited — a make.fun program/v1 entry.

## The image

A tiny lit city rides on the back of a colossal sea turtle, mid-stride
through a golden-hour ocean, sun low on the horizon, birds scattering.
Extreme scale contrast, one thrilling moment, drawn clean in flat vector
style so it still hits at 300 px wide.

## The program

`main.py` (Python 3.13, standard library only) draws the image pixel by
pixel — sky gradient, sun, sea, turtle, city, birds, spray — and encodes
it as a PNG. No network, no clock, no randomness: two runs write
byte-identical output.

Run it locally:

```
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

It writes `out/entry.png` (1024x1024, under 1 MiB).

## License

MIT — see LICENSE.
