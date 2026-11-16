"""I let the lion out of the movie for you — a lion bursting out of a cinema screen"""

import os
import sys

def get_image_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    primary = os.path.join(script_dir, "assets", "entry.jpg")
    if os.path.exists(primary):
        return primary
    return "/bot/assets/entry.jpg"

def get_output_dir():
    env_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if env_dir:
        return env_dir
    if os.path.exists("/output") and os.access("/output", os.W_OK):
        return "/output"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(script_dir, "out")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir

def main():
    src_path = get_image_path()
    out_dir = get_output_dir()
    dst_path = os.path.join(out_dir, "entry.png")
    
    with open(src_path, "rb") as f_in:
        data = f_in.read()
        
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("Source image is not a valid JPEG (missing FF D8 magic bytes)")

    with open(dst_path, "wb") as f_out:
        f_out.write(data)

if __name__ == "__main__":
    main()
