"""Render the synthetic SOWs to PDF, DOCX and Markdown so ingestion is tested
on real file formats, not just Python strings.

    python data/make_sample_docs.py
"""
from pathlib import Path

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

from sow_content import SOWS

OUT = Path(__file__).parent / "sample_sows"


def write_pdf(sow: dict, path: Path) -> None:
    styles = getSampleStyleSheet()
    story = [Paragraph(sow["title"], styles["Title"]), Spacer(1, 12)]
    for i, (heading, body) in enumerate(sow["sections"]):
        story += [Paragraph(heading, styles["Heading2"]), Paragraph(body, styles["BodyText"]), Spacer(1, 8)]
        if i == 4:  # force a second page so page metadata is exercised
            story.append(PageBreak())
    SimpleDocTemplate(str(path), pagesize=A4).build(story)


def write_docx(sow: dict, path: Path) -> None:
    doc = Document()
    doc.add_heading(sow["title"], level=0)
    for heading, body in sow["sections"]:
        doc.add_heading(heading, level=1)
        doc.add_paragraph(body)
    doc.save(str(path))


def write_md(sow: dict, path: Path) -> None:
    lines = [f"# {sow['title']}", ""]
    for heading, body in sow["sections"]:
        lines += [f"## {heading}", "", body, ""]
    path.write_text("\n".join(lines), encoding="utf-8")


WRITERS = {"pdf": write_pdf, "docx": write_docx, "md": write_md}

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for sow in SOWS:
        path = OUT / f"{sow['file']}.{sow['format']}"
        WRITERS[sow["format"]](sow, path)
        print("wrote", path)
