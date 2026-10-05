#!/usr/bin/env python3
"""Convert a Polygon problem package into this project's problem package.

A Polygon export is a whole problem *authoring* environment: LaTeX statement
templates, Windows checker/generator binaries, stress tests and generator
scripts. This judge needs five files:

    <slug>/statement.md   main.cpp   checker.cpp   config.json   tests/NN.in

so this script reads what the export already contains and writes those five,
leaving add_problem.py to compile the solution, generate the answer files and
validate the package.

    python3 engine/polygon_to_package.py bald-and-isabel-7 --out packages/
    cd <repo root> && python3 engine/add_problem.py --package_folder packages/<slug>

What it takes from the export
  problem.xml                  title, time limit, memory limit, tags, the
                               declared tests and which generator makes each one
  problem-properties.json       the statement, already split into sections
  checker (testlib source)     checker.cpp, with the problem's own globals.h
                               inlined so the package stays self-contained
  solution tagged "accepted"    main.cpp, the program that produces the answers
  tests/                       the hand-written test inputs, if they were
                               downloaded; everything else is regenerated from
                               the generator commands in problem.xml

Answers are never read from the export: add_problem.py regenerates them by
running main.cpp on every test.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from utils import fail
from package_spec import (
    CONFIG_JSON, CHECKER_CPP, MAIN_CPP, STATEMENT_MD, TESTS_DIR
)

ENGINE_DIR = Path(__file__).resolve().parent

# C++ source spellings seen in Polygon exports.
CPP_SUFFIXES = {".cpp", ".cc", ".cxx", ".c++"}
REPO_ROOT = ENGINE_DIR.parent

# Section macros used by the LaTeX templates that have no Markdown equivalent.
DROP_COMMANDS = (
    "InputFile",
    "OutputFile",
    "Example",
    "Note",
    "Hint",
    "Scoring",
    "Tutorial",
    "Copyright",
    "Begins",
    "ends",
)

# Footnote markers Polygon uses for definitions; kept as plain emphasis.
FOOTNOTE_COMMANDS = {
    "dagger": "*",
    "ddagger": "*",
    "S": "*",
}

INLINE_COMMANDS = {
    "textbf": "**",
    "textbf*": "**",
    "texttt": "`",
    "text": "",
    "emph": "*",
    "textit": "*",
    "underline": "",
    "textsc": "",
    "textrm": "",
    "mbox": "",
    "mathrm": "",
}

# ── LaTeX → Markdown ─────────────────────────────────────────────────────────


def find_command_body(text: str, command: str) -> tuple[str, str] | None:
    """Locates ``\\command{...}`` and returns (whole match, inner body)."""
    marker = "\\" + command + "{"
    start = text.find(marker)
    if start == -1:
        return None

    depth = 0
    for index in range(start + len(marker) - 1, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1], text[start + len(marker) : index]
    return None


def strip_environment(text: str, command: str) -> tuple[str, list[str]]:
    """Removes every ``\\command{...}`` wrapper, returning the bodies."""
    bodies: list[str] = []
    while (found := find_command_body(text, command)) is not None:
        whole, body = found
        text = text.replace(whole, body)
        bodies.append(body)
    return text, bodies


def tex_to_markdown(text: str) -> tuple[str, list[str]]:
    """Best-effort conversion of a Polygon statement section to Markdown.

    Math is left alone: the frontend renders ``$...$`` with KaTeX, and KaTeX
    understands the LaTeX macros the statements actually use.
    """
    footnotes: list[str] = []

    # Size wrappers carry the little footnotes ("a tree is a connected graph
    # ..."); pull them out so they become a note at the end of the section.
    for command in ("scriptsize", "footnotesize", "small", "normalsize", "large", "Large"):
        text, bodies = strip_environment(text, command)
        footnotes.extend(tex_to_markdown(body)[0] for body in bodies)

    for command in DROP_COMMANDS:
        text, _ = strip_environment(text, command)
        text = text.replace("\\" + command, "")

    # \rule{20em}{0.4pt} is the horizontal line statements use as a separator;
    # it is usually wrapped in math delimiters, so take those with it.
    text = re.sub(r"\$\s*\\rule\{[^}]*\}\{[^}]*\}\s*\$", "\n\n---\n\n", text)
    text = re.sub(r"\\rule\{[^}]*\}\{[^}]*\}", "\n\n---\n\n", text)

    for name, replacement in INLINE_COMMANDS.items():
        while (found := find_command_body(text, name)) is not None:
            whole, body = found
            if not replacement:
                text = text.replace(whole, body)
            else:
                text = text.replace(whole, f"{replacement}{body}{replacement}")

    # ``\t{JA}'' is Polygon's way of writing a quoted word; the \t is a stray
    # LaTeX tab escape and should not reach the browser.
    text = re.sub(r"\\t\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"``\s*([^`']*?)\s*''", r"`\1`", text)
    text = re.sub(r"``([^`]*)''", r"\1", text)

    # Images live next to the statement in the export and are not served by
    # the API, so drop the includegraphics and keep whatever surrounds it.
    text = re.sub(r"\\includegraphics(?:\[[^\]]*\])?\{[^}]*\}", "", text)
    text = re.sub(r"\\begin\{center\}.*?\\end\{center\}", "", text, flags=re.S)

    for name, replacement in FOOTNOTE_COMMANDS.items():
        text = re.sub(r"\$?\^\{" + name + r"\}\$?", replacement, text)
        text = text.replace("$^\\" + name + "$", replacement)

    text = re.sub(r"\\label\{[^}]*\}", "", text)
    text = text.replace("\\\\", "\n")
    text = text.replace("{}", "")

    # Collapse the whitespace the substitutions leave behind, but keep the
    # paragraph breaks that come from the original CRLF line breaks.
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    return text.strip(), footnotes


def section(title: str, body: str, footnotes: list[str]) -> str:
    if not body:
        return ""
    parts = [f"## {title}", "", body]
    if footnotes:
        parts += [""] + [f"- {line}" for line in footnotes if line]
    return "\n".join(parts).strip() + "\n\n"


# ── Polygon package reading ──────────────────────────────────────────────────


def read_xml(package: Path) -> ET.Element:
    xml_path = package / "problem.xml"
    if not xml_path.is_file():
        fail(f"{xml_path} is missing; is this a Polygon problem package?")
    return ET.parse(xml_path).getroot()


def first_text(element: ET.Element, path: str) -> str:
    node = element.find(path)
    return (node.text or "").strip() if node is not None and node.text else ""


def read_metadata(root: ET.Element) -> dict:
    testset = root.find("./judging/testset")
    if testset is None:
        fail("problem.xml has no <judging><testset>; nothing to convert.")

    memory_bytes = int(first_text(testset, "memory-limit") or 0)
    name_node = root.find("./names/name")
    title = (name_node.get("value", "") if name_node is not None else "").strip()
    return {
        "title": title or package_name(root),
        "time_limit": int(first_text(testset, "time-limit") or 1000),
        "memory_limit_mb": max(1, memory_bytes // (1024 * 1024)),
        "tags": [tag.get("value", "") for tag in root.findall("./tags/tag") if tag.get("value")],
        "tests": list(testset.findall("./tests/test")),
        "declared_tests": int(first_text(testset, "test-count") or 0),
    }


def package_name(root: ET.Element) -> str:
    return root.get("short-name", "problem")


def read_properties(package: Path, language: str) -> dict | None:
    """The pre-split statement. Polygon writes it next to the rendered copy."""
    directory = package / "statements" / language
    if not directory.is_dir():
        return None
    for path in sorted(directory.glob("problem-properties.json")):
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def find_asset(package: Path, root: ET.Element, xpath: str) -> Path | None:
    """Resolves an entry like ``<solution tag="accepted">`` to its source file.

    Polygon records the file either as an attribute of the node or as a nested
    ``<source path="..."/>`` child, so both spellings are accepted.
    """
    node = root.find(xpath)
    if node is None:
        return None

    relative = node.get("path") or node.get("source")
    if not relative:
        for child in node:
            if child.get("path"):
                relative = child.get("path")
                break
    if not relative:
        return None

    path = package / relative
    return path if path.is_file() else None


# ── Test generation ──────────────────────────────────────────────────────────


class GeneratorCache:
    """Compiles the exported generators once and runs them on demand."""

    def __init__(self, package: Path, workdir: Path):
        self.package = package
        self.binaries: dict[str, Path] = {}
        self.workdir = workdir

    # Generators are named freely in Polygon ("gen_random", "Gen", "grader", ...),
    # so every source in files/ is a candidate. The checker and validator are not
    # generators and are handled elsewhere.
    NON_GENERATOR = re.compile(r"^(check|checker|validator|validate|jchecker)\b", re.I)

    def compile_all(self) -> None:
        sources = sorted(
            source for source in (self.package / "files").glob("*.cpp")
            if not self.NON_GENERATOR.match(source.stem)
        )
        if not sources:
            return

        include = ENGINE_DIR / "include"
        for source in sources:
            binary = self.workdir / source.stem
            command = [
                "g++", "-O2", "-std=c++17",
                f"-I{self.package / 'files'}",
                f"-I{include}",
                str(source), "-o", str(binary),
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  ! could not build {source.name}: skipping it")
                continue
            self.binaries[source.stem.lower()] = binary

    def run(self, command: str) -> str | None:
        parts = command.split()
        if not parts:
            return None
        # Polygon records the command with the generator's own spelling, which
        # need not match the file name's case.
        binary = self.binaries.get(Path(parts[0]).name.lower())
        if binary is None:
            return None

        result = subprocess.run(
            [str(binary), *parts[1:]],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(f"  ! generator '{command}' failed: {result.stderr.strip()[:120]}")
            return None
        return result.stdout


# ── Conversion ───────────────────────────────────────────────────────────────


def inline_local_includes(source: str, package: Path) -> str:
    """Replaces ``#include "x.h"`` with the file's contents.

    The engine compiles a problem's checker from a temporary directory with only
    engine/include on the include path, so a checker that includes its own
    header would not build. Inlining keeps the package to the five files the
    spec lists.
    """
    pattern = re.compile(r'^\s*#include\s+"([^"]+)"\s*$', re.MULTILINE)

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name == "testlib.h":
            return match.group(0)  # provided by the engine
        header = package / "files" / name
        if header.is_file():
            body = inline_local_includes(header.read_text(encoding="utf-8"), package)
            return f"// ---- inlined from the Polygon export: {name} ----\n{body}"
        return match.group(0)

    return pattern.sub(replace, source)


def build_statement(package: Path, properties: dict | None, metadata: dict) -> str:
    title = metadata["title"]
    chunks = [f"# {title}\n"]

    if not properties:
        chunks.append(
            "_Converted without problem-properties.json: only the LaTeX "
            "statement was available._\n"
        )
        return "\n".join(chunks)

    legend, legend_notes = tex_to_markdown(properties.get("legend", ""))
    input_text, input_notes = tex_to_markdown(properties.get("input", ""))
    output_text, output_notes = tex_to_markdown(properties.get("output", ""))
    notes, notes_notes = tex_to_markdown(properties.get("notes", ""))
    tutorial, tutorial_notes = tex_to_markdown(properties.get("tutorial", ""))

    chunks.append(legend + "\n" if legend else "")
    chunks.append(section("Input", input_text, input_notes))
    chunks.append(section("Output", output_text, output_notes))
    chunks.append(section("Hints", tutorial, tutorial_notes))
    chunks.append(section("Note", notes, notes_notes))

    for index, sample in enumerate(properties.get("sampleTests", []) or [], start=1):
        sample_input = (sample.get("input") or "").replace("\r\n", "\n").strip()
        sample_output = (sample.get("output") or "").replace("\r\n", "\n").strip()
        if not sample_input:
            continue
        chunks.append(f"## Example {index}\n")
        if sample_input:
            chunks.append("**Input**\n")
            chunks.append(f"```\n{sample_input}\n```\n")
        if sample_output:
            chunks.append("**Output**\n")
            chunks.append(f"```\n{sample_output}\n```\n")

    return "\n".join(chunk for chunk in chunks if chunk).strip() + "\n"


def copy_tests(
    package: Path,
    metadata: dict,
    destination: Path,
    generators: GeneratorCache,
    max_tests: int | None,
) -> list[str]:
    """Writes tests/00.in … from the export, regenerating generated tests."""
    warnings: list[str] = []
    written = 0

    for index, test in enumerate(metadata["tests"]):
        if max_tests is not None and written >= max_tests:
            warnings.append(f"stopped after {max_tests} tests (--max-tests)")
            break

        number = index + 1
        command = (test.get("cmd") or "").strip()
        manual_file = package / "tests" / f"{number:02d}"

        if command:
            data = generators.run(command)
            if data is None:
                warnings.append(f"test {number:02d}: generator '{command}' produced nothing")
                continue
        elif manual_file.is_file():
            data = manual_file.read_text(encoding="utf-8", errors="replace")
        else:
            warnings.append(f"test {number:02d}: hand-written input not in the export")
            continue

        (destination / f"{written:02d}.in").write_text(data, encoding="utf-8")
        written += 1

    if written == 0:
        fail("no tests could be produced from this export.")

    expected = metadata["declared_tests"]
    if written < expected and max_tests is None:
        warnings.append(f"export declares {expected} tests, {written} were produced")
    return warnings


def convert(package: Path, slug: str, out_root: Path, max_tests: int | None) -> Path:
    if not package.is_dir():
        fail(f"'{package}' is not a directory.")

    root = read_xml(package)
    metadata = read_metadata(root)
    properties = read_properties(package, "english")

    destination = out_root / slug
    if destination.exists():
        fail(f"'{destination}' already exists; remove it or pass a different --out.")
    (destination / TESTS_DIR).mkdir(parents=True)

    statement = build_statement(package, properties, metadata)
    (destination / STATEMENT_MD).write_text(statement, encoding="utf-8")

    config = {
        "title": metadata["title"],
        "time_limit": metadata["time_limit"],
        "memory_limit": metadata["memory_limit_mb"],
        "tags": metadata["tags"],
    }
    (destination / CONFIG_JSON).write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # The engine only judges C++, and an export usually carries solutions in
    # several languages at once, with the 'accepted' tag on whichever language
    # the setter submitted. Picking the first solution node regardless of
    # language copies a .py or .java into main.cpp and only fails later, at
    # compile time, so choose on the declared type and fall back to a C++ one.
    candidates: list[tuple[bool, str, Path]] = []
    for node in root.iter("solution"):
        tag = (node.get("tag") or "").lower()
        for source in node.iter("source"):
            relative = source.get("path")
            if not relative:
                continue
            path = package / relative
            if not path.is_file():
                continue
            declared = (source.get("type") or "").lower()
            is_cpp = declared.startswith("cpp") or path.suffix.lower() in CPP_SUFFIXES
            if is_cpp:
                candidates.append((tag == "accepted", tag or "main", path))

    if not candidates:
        fail(
            "no C++ solution source in the export. Tag a C++ solution "
            "'accepted' on Polygon (the engine judges C++ only)."
        )

    candidates.sort(key=lambda item: (not item[0], item[1]))
    chosen_solution = candidates[0][2]
    shutil.copyfile(chosen_solution, destination / MAIN_CPP)

    checker = (
        find_asset(package, root, "./assets/checker/source")
        or find_asset(package, root, "./assets/validators/validator/source")
    )
    if checker is None:
        checker = package / "check.cpp"
    if not checker.is_file():
        fail("no checker source in the export.")
    (destination / CHECKER_CPP).write_text(
        inline_local_includes(checker.read_text(encoding="utf-8"), package),
        encoding="utf-8",
    )

    with tempfile.TemporaryDirectory() as tmp:
        generators = GeneratorCache(package, Path(tmp))
        generators.compile_all()
        warnings = copy_tests(package, metadata, destination / "tests", generators, max_tests)

    print(f"Package written to {destination}")
    print(f"  title       {metadata['title']}")
    print(f"  limits      {metadata['time_limit']} ms, {metadata['memory_limit_mb']} MB")
    print(f"  tags        {', '.join(metadata['tags']) or '(none)'}")
    print(f"  tests       {len(list((destination / 'tests').glob('*.in')))}")
    print(f"  solution    {chosen_solution.relative_to(package)}")
    print(f"  checker     {checker.relative_to(package)}")
    for warning in warnings:
        print(f"  ! {warning}")

    print("\nNext:")
    print(f"  python3 engine/add_problem.py --package_folder {destination}")
    print("  cd backend && .venv/bin/python init_db.py")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("package", type=Path, help="extracted Polygon package directory")
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "packages",
        help="where to write the converted package (default: ./packages)",
    )
    parser.add_argument("--slug", help="slug for the new package (default: the export directory name)")
    parser.add_argument(
        "--max-tests",
        type=int,
        default=None,
        help="stop after this many tests (the engine accepts at most 100)",
    )
    args = parser.parse_args()

    package = args.package.resolve()
    slug = args.slug or package.name
    if not re.fullmatch(r"[A-Za-z0-9_-]+", slug):
        fail(f"Invalid slug '{slug}': letters, numbers, hyphens and underscores only.")

    convert(package, slug, args.out.resolve(), args.max_tests)


if __name__ == "__main__":
    main()