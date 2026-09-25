"""Build a manual-install ZIP without caches, local config or test data."""

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
integration = root / "custom_components" / "esptimecast"
version = json.loads((integration / "manifest.json").read_text())["version"]
output = root / "dist" / f"esptimecast-{version}.zip"
output.parent.mkdir(exist_ok=True)
with ZipFile(output, "w", ZIP_DEFLATED) as archive:
    for path in sorted(integration.rglob("*")):
        if path.is_file() and path.suffix in (".py", ".json", ".yaml", ".png"):
            archive.write(path, path.relative_to(root))
    for folder in ("blueprints", "examples"):
        for path in sorted((root / folder).rglob("*")):
            if path.is_file() and path.suffix in (".yaml", ".md"):
                archive.write(path, path.relative_to(root))
    for name in ("README.md", "LICENSE", "hacs.json"):
        archive.write(root / name, name)
print(output)
