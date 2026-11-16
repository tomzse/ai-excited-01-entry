import os
import sys

def main():
    # Resolve script directory from __file__
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Image path resolution: relative to script location, fallback to /bot/assets/entry.jpg
    image_path = os.path.join(script_dir, "assets", "entry.jpg")
    if not os.path.exists(image_path):
        image_path = "/bot/assets/entry.jpg"

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Source image not found at {image_path}")

    # Output directory resolution:
    # 1. MAKEFUN_OUTPUT_DIR env var if set
    # 2. /output if it exists and is writable
    # 3. "out" directory located next to the script itself
    env_out = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if env_out:
        out_dir = env_out
    elif os.path.exists("/output") and os.access("/output", os.W_OK):
        out_dir = "/output"
    else:
        out_dir = os.path.join(script_dir, "out")

    # Create output directory if it does not exist
    os.makedirs(out_dir, exist_ok=True)

    dest_path = os.path.join(out_dir, "entry.png")

    # Write byte-for-byte
    with open(image_path, "rb") as f_in:
        data = f_in.read()

    with open(dest_path, "wb") as f_out:
        f_out.write(data)

if __name__ == "__main__":
    main()
