#!/usr/bin/env python3
"""Generate and atomically publish a validated static C4 architecture site."""

from __future__ import annotations

import argparse
from html import escape
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from render_c4 import html_page, render  # noqa: E402
from validate_canonical_projection import validate_view  # noqa: E402


def child_path(root: Path, value: str, label: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        raise ValueError(f"{label} must be relative: {value}")
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"{label} escapes its root: {value}")
    return resolved


def validate_site(site: object) -> dict:
    if not isinstance(site, dict):
        raise ValueError("render plan requires a site object")
    for field in ("title", "description"):
        if not isinstance(site.get(field), str) or not site[field].strip():
            raise ValueError(f"site.{field} is required")
    if site["title"].strip().lower() in {"architecture", "c4 architecture", "subject architecture"}:
        raise ValueError("site.title must name the modelled subject")
    systems = site.get("systems")
    if not isinstance(systems, list) or not systems:
        raise ValueError("site.systems requires at least one software-system summary")
    for index, system in enumerate(systems):
        if not isinstance(system, dict):
            raise ValueError(f"site.systems[{index}] must be an object")
        for field in ("id", "name", "description"):
            if not isinstance(system.get(field), str) or not system[field].strip():
                raise ValueError(f"site.systems[{index}].{field} is required")
    ids = [system["id"] for system in systems]
    if len(ids) != len(set(ids)):
        raise ValueError("site.systems IDs must be unique")
    return site


def index_page(site: dict, entries: list[tuple[dict, dict]]) -> str:
    title = str(site.get("title") or "Architecture")
    description = str(site.get("description") or "Navigable C4 architecture views.")
    systems = site.get("systems") if isinstance(site.get("systems"), list) else []
    system_cards = "".join(
        f'<article><h2>{escape(str(item.get("name", "Software system")))}</h2><p>{escape(str(item.get("description", "")))}</p></article>'
        for item in systems if isinstance(item, dict)
    )
    view_cards = "".join(
        f'<article><span>{escape(str(view["diagramType"]))}</span><h2>{escape(str(view["title"]))}</h2>'
        f'<p>{escape(str(view.get("description", "")))}</p><a href="{escape(str(item["html"]))}">Open diagram <span aria-hidden="true">→</span></a></article>'
        for item, view in entries
    )
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)}</title><style>
:root{{--ink:#172033;--muted:#52606d;--blue:#075ea8;--line:#d8e0e8;--panel:#fff;--wash:#f4f7fa}}*{{box-sizing:border-box}}body{{margin:0;font:15px/1.55 Arial,sans-serif;color:var(--ink);background:var(--wash)}}main{{width:min(1180px,calc(100% - 32px));margin:auto;padding:54px 0}}header{{max-width:850px;margin-bottom:34px}}h1{{font-size:clamp(2rem,5vw,3.5rem);line-height:1.05;margin:0 0 14px}}header p{{font-size:1.1rem;color:var(--muted)}}h2{{margin:7px 0;font-size:1.15rem}}h3{{margin-top:38px;font-size:1.35rem}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}}article{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px;box-shadow:0 2px 10px #1720330b}}article span{{font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;color:var(--blue);font-weight:700}}article p{{color:var(--muted)}}a{{color:var(--blue);font-weight:700}}footer{{margin-top:42px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted)}}
</style></head><body><main><header><h1>{escape(title)}</h1><p>{escape(description)}</p></header>{('<h3>Software systems</h3><div class="grid">'+system_cards+'</div>') if system_cards else ''}<h3>Architecture views</h3><div class="grid">{view_cards}</div><footer>Static architecture documentation generated from validated C4 view definitions.</footer></main></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    plan_path = args.plan.resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    project_root = (plan_path.parent / plan.get("projectRoot", ".")).resolve()
    architecture_root = child_path(project_root, str(plan.get("architectureRoot", "architecture")), "architectureRoot")
    canonical_path = child_path(project_root, str(plan.get("canonical", ".architecture-model/canonical.json")), "canonical")
    if not canonical_path.is_file():
        raise ValueError(f"canonical architecture model is missing: {canonical_path}")
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    site = validate_site(plan.get("site"))

    view_entries: list[tuple[dict, dict]] = []
    rendered: list[tuple[str, str]] = []
    system_ids = {item["id"] for item in site["systems"]}
    core_coverage: dict[str, set[str]] = {system_id: set() for system_id in system_ids}
    output_paths: set[str] = set()
    views = plan.get("views")
    if not isinstance(views, list) or not views:
        raise ValueError("render plan requires a non-empty views array")
    for index, item in enumerate(views):
        if not isinstance(item, dict):
            raise ValueError(f"views[{index}] must be an object")
        system_id = item.get("systemId")
        if system_id not in system_ids:
            raise ValueError(f"views[{index}].systemId must reference site.systems")
        for field in ("source", "svg", "html"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"views[{index}].{field} is required")
        source = child_path(project_root, item["source"], f"views[{index}].source")
        view = json.loads(source.read_text(encoding="utf-8"))
        projection_failures = validate_view(canonical, view, str(source))
        if projection_failures:
            raise ValueError("C4 provenance validation failed:\n- " + "\n- ".join(projection_failures))
        svg_relative = Path(item["svg"])
        html_relative = Path(item["html"])
        if svg_relative.suffix.lower() != ".svg" or html_relative.suffix.lower() != ".html":
            raise ValueError(f"views[{index}] outputs must use .svg and .html extensions")
        normalized_outputs = {str(svg_relative).replace("\\", "/"), str(html_relative).replace("\\", "/")}
        if output_paths & normalized_outputs:
            raise ValueError(f"views[{index}] reuses an output path")
        output_paths.update(normalized_outputs)
        # Validate output paths now; actual writes happen only in staging.
        child_path(architecture_root, str(svg_relative), f"views[{index}].svg")
        child_path(architecture_root, str(html_relative), f"views[{index}].html")
        svg_reference = os.path.relpath(svg_relative, html_relative.parent).replace("\\", "/")
        rendered.append((str(svg_relative), render(view)))
        rendered.append((str(html_relative), html_page(view, svg_reference)))
        view_entries.append((item, view))
        if view.get("diagramType") in {"System Context", "Container"}:
            core_coverage[system_id].add(view["diagramType"])

    for system_id, covered in core_coverage.items():
        missing = {"System Context", "Container"} - covered
        if missing:
            raise ValueError(f"system {system_id} is missing required views: {', '.join(sorted(missing))}")

    architecture_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{architecture_root.name}-staging-", dir=architecture_root.parent))
    backup: Path | None = None
    try:
        for relative, content in rendered:
            output = child_path(staging, relative, "rendered output")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(content, encoding="utf-8")
        (staging / "index.html").write_text(index_page(site, view_entries), encoding="utf-8")

        validator = SCRIPT_DIR / "validate_c4_package.py"
        result = subprocess.run([sys.executable, str(validator), str(staging)], check=False)
        if result.returncode:
            print("Generated site failed validation; public architecture output was not changed.", file=sys.stderr)
            return result.returncode

        if architecture_root.exists():
            backup = Path(tempfile.mkdtemp(prefix=f".{architecture_root.name}-backup-", dir=architecture_root.parent))
            backup.rmdir()
            os.replace(architecture_root, backup)
        try:
            os.replace(staging, architecture_root)
        except Exception:
            if backup and backup.exists() and not architecture_root.exists():
                os.replace(backup, architecture_root)
            raise
        if backup and backup.exists():
            shutil.rmtree(backup)
        print(f"Published validated architecture site: {architecture_root}")
        return 0
    finally:
        if staging.exists():
            shutil.rmtree(staging)


if __name__ == "__main__":
    raise SystemExit(main())
