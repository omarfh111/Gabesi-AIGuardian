"""
preprocess_docx.py

Converts the PDL Gabes .docx file into a clean markdown file
where every table is properly preserved as a markdown table.

This MUST run before ingestion. Without it, Chonkie will mangle
all 37+ tables in the document, destroying critical agricultural
and environmental data.

Usage:
    python preprocess_docx.py

Output:
    data/processed/PDL_GABES_clean.md
"""

import re
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from tqdm import tqdm


# ── paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH  = BASE_DIR / "data/pdl_reports/PDL GABES Rapport de pré diagnostic .20.03.2023.docx"
OUTPUT_DIR  = BASE_DIR / "data/processed"
OUTPUT_PATH = OUTPUT_DIR / "PDL_GABES_clean.md"


# ── helpers ────────────────────────────────────────────────────────────────

def get_cell_text(cell) -> str:
    """Extract clean text from a table cell, collapsing internal newlines."""
    text = " ".join(p.text.strip() for p in cell.paragraphs if p.text.strip())
    return text.replace("|", "\\|")  # escape pipes so markdown doesn't break


def table_to_markdown(table) -> str:
    """
    Convert a python-docx Table object to a GitHub-flavored markdown table.

    Handles:
    - Merged cells (uses first occurrence, skips duplicates in same row)
    - Empty rows (skipped)
    - Multi-row headers (first non-empty row becomes the header)
    """
    rows_data = []

    for row in table.rows:
        cells = [get_cell_text(cell) for cell in row.cells]

        # Deduplicate merged cells within a row
        # python-docx repeats the same cell object for merged spans
        seen_ids = []
        deduped = []
        for cell in row.cells:
            cell_id = id(cell)
            if cell_id not in seen_ids:
                seen_ids.append(cell_id)
                deduped.append(get_cell_text(cell))

        if any(c.strip() for c in deduped):  # skip fully empty rows
            rows_data.append(deduped)

    if not rows_data:
        return ""

    # Pad all rows to the same column count
    max_cols = max(len(r) for r in rows_data)
    padded = [r + [""] * (max_cols - len(r)) for r in rows_data]

    # Build markdown
    lines = []

    # Header row
    header = padded[0]
    lines.append("| " + " | ".join(header) + " |")

    # Separator
    lines.append("| " + " | ".join(["---"] * max_cols) + " |")

    # Data rows
    for row in padded[1:]:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def iter_block_items(document):
    """
    Yield each paragraph and table in document order.
    python-docx normally gives you paragraphs and tables separately,
    losing their relative order. This iterates the raw XML to preserve it.

    Yields tuples of ('paragraph', paragraph_obj) or ('table', table_obj).
    """
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    parent = document.element.body
    for child in parent.iterchildren():
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "p":
            yield "paragraph", Paragraph(child, document)
        elif tag == "tbl":
            yield "table", Table(child, document)


def clean_paragraph_text(text: str) -> str:
    """
    Light cleaning:
    - Strip leading/trailing whitespace
    - Collapse multiple spaces
    - Remove null characters that sometimes appear in docx exports
    """
    text = text.replace("\x00", "").replace("\xa0", " ")
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def paragraph_to_markdown(para) -> str:
    """
    Convert a paragraph to markdown, preserving heading levels.
    Heading 1 → #, Heading 2 → ##, etc. up to H4.
    Normal text → plain text.
    """
    text = clean_paragraph_text(para.text)
    if not text:
        return ""

    style_name = para.style.name if para.style else ""

    if "Heading 1" in style_name:
        return f"# {text}"
    elif "Heading 2" in style_name:
        return f"## {text}"
    elif "Heading 3" in style_name:
        return f"### {text}"
    elif "Heading 4" in style_name:
        return f"#### {text}"
    else:
        return text


# ── main ───────────────────────────────────────────────────────────────────

def preprocess_docx(input_path: Path, output_path: Path) -> None:
    print(f"\n{'='*60}")
    print(f"  PDL Gabès Preprocessing")
    print(f"{'='*60}")
    print(f"  Input:  {input_path}")
    print(f"  Output: {output_path}")
    print(f"{'='*60}\n")

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}\n"
            f"Make sure you're running this script from the project root (farmer/)"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = Document(str(input_path))

    blocks = list(iter_block_items(doc))
    print(f"  Found {len(blocks)} blocks (paragraphs + tables)\n")

    output_lines = []
    table_count = 0
    para_count = 0
    empty_count = 0

    for block_type, block in tqdm(blocks, desc="Processing blocks"):
        if block_type == "paragraph":
            md = paragraph_to_markdown(block)
            if md:
                output_lines.append(md)
                para_count += 1
            else:
                empty_count += 1

        elif block_type == "table":
            table_count += 1
            md_table = table_to_markdown(block)
            if md_table:
                # Add spacing around tables so chunker treats them as discrete units
                output_lines.append("")
                output_lines.append(md_table)
                output_lines.append("")

    # Write output
    final_content = "\n".join(output_lines)

    # Final cleanup: collapse 3+ consecutive blank lines into 2
    final_content = re.sub(r"\n{3,}", "\n\n", final_content)

    output_path.write_text(final_content, encoding="utf-8")

    # ── report ──
    output_size_kb = output_path.stat().st_size / 1024
    print(f"\n{'='*60}")
    print(f"  DONE")
    print(f"{'='*60}")
    print(f"  Paragraphs processed : {para_count}")
    print(f"  Empty paragraphs skipped: {empty_count}")
    print(f"  Tables converted     : {table_count}")
    print(f"  Output size          : {output_size_kb:.1f} KB")
    print(f"  Output file          : {output_path}")
    print(f"{'='*60}\n")

    # ── sanity check ──
    print("  Sanity check — searching for key table data in output...")
    checks = [
        ("Bahria oasis data",    "Bahria"),
        ("GCT production data",  "GCT"),
        ("Oasis table",          "Ouesta"),
        ("Population data",      "Sidi Boulbaba"),
        ("Water resources",      "nappe"),
        ("Fluoride pollution",   "phosphogypse"),
    ]

    all_passed = True
    for label, keyword in checks:
        found = keyword.lower() in final_content.lower()
        status = "✓" if found else "✗ MISSING"
        print(f"    {status}  {label} ('{keyword}')")
        if not found:
            all_passed = False

    if all_passed:
        print("\n  All sanity checks passed. Ready for ingestion.")
    else:
        print("\n  WARNING: Some checks failed. Review the output file.")

    print()


if __name__ == "__main__":
    preprocess_docx(INPUT_PATH, OUTPUT_PATH)