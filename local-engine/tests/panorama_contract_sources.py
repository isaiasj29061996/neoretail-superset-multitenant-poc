"""Read the canonical implementations used by Panorama source contracts."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read_panorama(*modules):
    paths = [ROOT / "superset/bootstrap_panorama.py"]
    paths.extend(ROOT / "superset/neoretail_bootstrap/panorama" / f"{name}.py" for name in modules)
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)
