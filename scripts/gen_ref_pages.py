"""Generate API reference pages from the tickerscope package structure."""

from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()
root = Path(__file__).parent.parent
src = root / "src"

SKIP_MODULES = {"__pycache__", "__main__"}

MODULE_DESCRIPTIONS = {
    "auth": "JWT resolution, cookie extraction, and token validation.",
    "client": "Sync and async clients for the MarketSurge GraphQL API.",
    "dates": "Timezone-aware date parsing utilities.",
    "exceptions": "Structured error hierarchy with serialization support.",
    "models": "Frozen dataclass models for all API responses.",
    "parsing": "Response parsers that transform raw JSON into typed models.",
    "queries": "GraphQL query loading and constants.",
    "serialization": "Base class for dict/JSON round-trip serialization.",
}

init_pages: list[tuple[list[str], Path, Path]] = []
child_modules: dict[str, list[tuple[str, str]]] = {}

for path in sorted(src.rglob("*.py")):
    module_path = path.relative_to(src).with_suffix("")
    doc_path = path.relative_to(src).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = list(module_path.parts)

    if any(skip in parts for skip in SKIP_MODULES):
        continue

    is_init = parts[-1] == "__init__"

    if is_init:
        parts = parts[:-1]
        if not parts:
            continue
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
        init_pages.append((parts, doc_path, full_doc_path))
        pkg_key = ".".join(parts)
        child_modules.setdefault(pkg_key, [])
        continue

    nav_parts = []
    for part in parts:
        display = (
            part.lstrip("_").replace("_", " ").title() if part.startswith("_") else part
        )
        nav_parts.append(display)

    nav[nav_parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        fd.write(f"::: {ident}\n")

    mkdocs_gen_files.set_edit_path(full_doc_path, path.relative_to(root))

    if len(parts) > 1:
        pkg_key = ".".join(parts[:-1])
        mod_name = parts[-1]
        display = mod_name.lstrip("_").replace("_", " ").title()
        child_modules.setdefault(pkg_key, []).append((mod_name, display))

for parts, doc_path, full_doc_path in init_pages:
    nav_parts = []
    for part in parts:
        display = (
            part.lstrip("_").replace("_", " ").title() if part.startswith("_") else part
        )
        nav_parts.append(display)

    nav[nav_parts] = doc_path.as_posix()

    pkg_key = ".".join(parts)
    children = child_modules.get(pkg_key, [])

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        fd.write(f"# {pkg_key}\n\n")
        if children:
            fd.write("| Module | Description |\n")
            fd.write("|--------|-------------|\n")
            for mod_name, display in sorted(children, key=lambda x: x[1]):
                clean = mod_name.lstrip("_")
                desc = MODULE_DESCRIPTIONS.get(clean, "")
                fd.write(f"| [{display}]({mod_name}.md) | {desc} |\n")
            fd.write("\n")

    init_path = src / Path(*parts) / "__init__.py"
    mkdocs_gen_files.set_edit_path(full_doc_path, init_path.relative_to(root))

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
