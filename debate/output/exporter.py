from __future__ import annotations

import json
from pathlib import Path

from ..models import DebateResult


def export_result(result: DebateResult, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path
