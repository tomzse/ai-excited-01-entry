"""The Toy Box Rex — a colossal LEGO T-Rex bursting out of a toy box"""

import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))

img_path = os.path.join(script_dir, "assets", "entry.jpg")
if not os.path.exists(img_path):
    img_path = "/bot/assets/entry.jpg"

if "MAKEFUN_OUTPUT_DIR" in os.environ and os.environ["MAKEFUN_OUTPUT_DIR"]:
    output_dir = os.environ["MAKEFUN_OUTPUT_DIR"]
elif os.path.exists("/output") and os.access("/output", os.W_OK):
    output_dir = "/output"
else:
    output_dir = os.path.join(script_dir, "out")

os.makedirs(output_dir, exist_ok=True)
out_path = os.path.join(output_dir, "entry.png")

with open(img_path, "rb") as f_in:
    data = f_in.read()

if not data.startswith(b"\xff\xd8"):
    raise ValueError("Source image is not a valid JPEG (missing FF D8 header)")

with open(out_path, "wb") as f_out:
    f_out.write(data)
