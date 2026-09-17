from __future__ import annotations

import os
from pathlib import Path

# Tests can run either from the host checkout or from inside the local-engine
# container. Inside Docker the repository root is mounted read-only at /repo so
# contract tests can inspect compose, Superset and embedded-app files without
# giving the engine write access to the project checkout.
REPO_ROOT = Path(os.getenv("NEORETAIL_REPO_ROOT", Path(__file__).resolve().parents[2]))
os.environ.setdefault("NEORETAIL_REPO_ROOT", str(REPO_ROOT))
