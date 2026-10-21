import sys
from pathlib import Path

# Automatically ensure workspace root is on sys.path so 'backend.app' imports succeed
# regardless of whether the user runs from project root or inside backend/
_backend_dir = Path(__file__).resolve().parent.parent
_repo_root = _backend_dir.parent

for _p in (str(_repo_root), str(_backend_dir)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
