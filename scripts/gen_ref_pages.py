"""Generate API reference pages from the tickerscope package structure."""

from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()
root = Path(__file__).parent.parent
src = root / "src"

SKIP_MODULES = {"__pycache__", "__main__"}

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

    nav_parts = []
    for part in parts:
        display = (
            part.lstrip("_").replace("_", " ").title() if part.startswith("_") else part
        )
        nav_parts.append(display)

    nav[nav_parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        if is_init:
            fd.write(f"::: {ident}\n")
            fd.write("    options:\n")
            fd.write("      members: false\n")
        else:
            fd.write(f"::: {ident}\n")

    mkdocs_gen_files.set_edit_path(full_doc_path, path.relative_to(root))

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
