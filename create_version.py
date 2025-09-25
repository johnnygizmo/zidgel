import tomllib
from pathlib import Path

version = "Error"
manifest_path = Path("blender_manifest.toml")
if manifest_path.exists():
    with open(manifest_path, "rb") as f:
        manifest_data = tomllib.load(f)
    version = manifest_data.get("version", "Error")

    with open("version.py", "w", encoding="utf-8") as f:
        f.write(f'VERSION = "{version}"\n')
else:
    print("Manifest file not found.")