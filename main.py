"""The Toy Box Rex — a colossal LEGO T-Rex bursting out of a toy box"""

import os

script_dir = os.path.dirname(os.path.abspath(__file__))

image_path = os.path.join(script_dir, "assets", "entry.jpg")
if not os.path.exists(image_path):
    image_path = "/bot/assets/entry.jpg"

with open(image_path, "rb") as src:
    data = src.read()

if not data.startswith(b"\xff\xd8"):
    raise ValueError(f"Source image at {image_path} does not start with JPEG magic bytes FF D8")

env_out = os.environ.get("MAKEFUN_OUTPUT_DIR")
if env_out:
    output_dir = env_out
elif os.path.exists("/output") and os.access("/output", os.W_OK):
    output_dir = "/output"
else:
    output_dir = os.path.join(script_dir, "out")

os.makedirs(output_dir, exist_ok=True)

output_file = os.path.join(output_dir, "entry.png")

with open(output_file, "wb") as dst:
    dst.write(data)
