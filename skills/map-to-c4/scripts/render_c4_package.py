#!/usr/bin/env python3
"""Regenerate a confirmed C4 package from a deterministic render plan."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from render_c4 import html_page, render  # noqa: E402
from validate_canonical_projection import validate_view  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    plan_path = args.plan.resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    project_root = (plan_path.parent / plan.get("projectRoot", ".")).resolve()
    architecture_root = project_root / plan.get("architectureRoot", "architecture")
    canonical_path = project_root / plan.get("canonical", ".architecture-model/canonical.json")
    if not canonical_path.is_file():
        raise ValueError(f"canonical architecture model is missing: {canonical_path}")
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))

    pending: list[tuple[Path, str]] = []
    for item in plan.get("views", []):
        source = project_root / item["source"]
        svg_path = architecture_root / item["svg"]
        html_path = architecture_root / item["html"]
        view = json.loads(source.read_text(encoding="utf-8"))
        projection_failures = validate_view(canonical, view, str(source))
        if projection_failures:
            raise ValueError("canonical projection validation failed:\n- " + "\n- ".join(projection_failures))
        svg = render(view)
        svg_reference = os.path.relpath(svg_path, html_path.parent).replace("\\", "/")
        pending.append((svg_path, svg))
        pending.append((html_path, html_page(view, svg_reference)))

    # Render every view successfully before replacing any public artifact.
    for path, content in pending:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"Wrote {path}")

    validator = SCRIPT_DIR / "validate_c4_package.py"
    result = subprocess.run([sys.executable, str(validator), str(architecture_root)], check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
