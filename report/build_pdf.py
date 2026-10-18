"""Build report/REPORT.pdf from report/REPORT.md with headless Google Chrome, and print the page count.

It uses the shared theme of the visuals and the video (visuals/theme.css). Only the Markdown that REPORT.md uses is
supported: headings, paragraphs, bullet and numbered lists, tables, images, links, bold, italics and inline code.
An image may carry a size as its title (`![caption](file.png "large")`: large, big, medium, small, or side for a
small figure to the right of its text), and a line
`<!-- page -->` starts a new page.
A GIF is shown by its PNG still. A figure that doesn't exist yet is drawn as a grey box with its file name, so the
page count stays honest while the visuals are being made.

Usage: .venv/bin/python report/build_pdf.py
"""
import html
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SOURCE, PAGE, PDF = HERE / "REPORT.md", HERE / "REPORT.html", HERE / "REPORT.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

THEME = HERE.parent / "visuals" / "theme.css"
PRINT_CSS = """
@page { size: A4; margin: 14mm 15mm 14mm 15mm; }
html, body { background: #fff; }
body { font: 9.6pt/1.38 var(--font); color: var(--ink); margin: 0; -webkit-print-color-adjust: exact; }
h1 { font-size: 17pt; letter-spacing: -0.2pt; margin: 0 0 0.8mm; }
.subtitle { font-size: 10.5pt; margin: 0 0 0.6mm; }
.subtitle + p { font-size: 8.6pt; color: var(--muted); margin-bottom: 2mm; }
h2 { break-after: avoid; font-size: 11.5pt; margin: 3.2mm 0 1.2mm; padding-bottom: 0.6mm;
     border-bottom: 0.6pt solid var(--axis); }
h2::before { content: ""; display: inline-block; width: 2.2mm; height: 2.2mm; margin-right: 1.6mm;
             border-radius: 0.5mm; background: var(--blue); }
p { margin: 0 0 1.6mm; }
ul, ol { margin: 0 0 1.6mm; padding-left: 5mm; }
li { margin: 0 0 0.6mm; }
li::marker { color: var(--ink-2); }
code { font: 8.6pt Menlo, monospace; background: var(--panel); padding: 0 0.6mm; border-radius: 1mm; }
.link { color: var(--blue); }
table { break-inside: avoid; border-collapse: collapse; margin: 1mm 0 2mm; font-size: 8.8pt; width: 100%; }
th, td { border-bottom: 0.4pt solid var(--grid); padding: 0.5mm 1.6mm; text-align: left; }
th { background: var(--panel); color: var(--ink-2); font-weight: 600; }
th, td:not(:last-child) { white-space: nowrap; }
td strong { color: var(--aqua); }
figure { margin: 1.5mm 0 2.5mm; text-align: center; break-inside: avoid; }
figure img { max-width: 100%; border-radius: 1.5mm; }
figure.large img { max-height: 104mm; }
figure.big img { max-height: 84mm; }
figure.medium img { max-height: 62mm; }
figure.small img { max-height: 46mm; }
figure.large .missing { height: 104mm; width: 185mm; }
figure.medium .missing { height: 62mm; width: 110mm; }
figure.small .missing { height: 46mm; width: 82mm; }
figure.side { float: right; width: 54%; margin: 0.5mm 0 1.5mm 4mm; }
h2 { clear: both; }
.page-break { break-before: page; }
figcaption { font-size: 8.4pt; color: var(--ink-2); margin-top: 0.8mm; }
.row { display: flex; gap: 4mm; justify-content: center; align-items: flex-end; }
.row figure { flex: 1; }
.missing { display: inline-flex; align-items: center; justify-content: center; max-width: 100%;
           background: var(--panel); color: var(--muted); }
"""


def inline(text):
    """Escape the text, then apply code, bold and italics."""
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^]]+)\]\([^)]+\)", r'<span class="link">\1</span>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"(?<![\w*])\*(?!\s)(.+?)\*(?!\w)", r"<em>\1</em>", text)


IMAGE = r'!\[(.*)\]\((\S+)(?: "(\w+)")?\)'


def figure(alt, src, size="medium"):
    """One figure with its caption; an animated GIF is shown by its settled PNG still, and a missing file as a
    grey box."""
    path = (HERE / src).resolve()
    path = path.with_suffix(".png") if path.suffix == ".gif" else path
    body = f'<img src="{path.as_uri()}">' if path.exists() else f'<span class="missing">{html.escape(src)}</span>'
    return f'<figure class="{size}">{body}<figcaption>{inline(alt)}</figcaption></figure>'


def table(rows):
    """A Markdown table: header row, separator row, body rows."""
    cells = [[c.strip() for c in row.strip().strip("|").split("|")] for row in rows]
    head = "".join(f"<th>{inline(c)}</th>" for c in cells[0])
    body = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>" for row in cells[2:])
    return f"<table><tr>{head}</tr>{body}</table>"


def blocks(lines):
    """Split the Markdown into blocks separated by blank lines."""
    block = []
    for line in lines + [""]:
        if line.strip():
            block.append(line)
        elif block:
            yield block
            block = []


def items(block, marker):
    """List items, joining continuation lines to the item above."""
    out = []
    for line in block:
        if re.match(marker, line):
            out.append(re.sub(marker, "", line))
        else:
            out[-1] += " " + line.strip()
    return "".join(f"<li>{inline(i)}</li>" for i in out)


def render(block):
    """One block of Markdown as HTML."""
    first = block[0]
    if first.strip() == "<!-- page -->":
        return '<div class="page-break"></div>'
    images = [re.fullmatch(IMAGE, line.strip()) for line in block]
    if all(images):
        figures = "".join(figure(*filter(None, image.groups())) for image in images)
        return f'<div class="row">{figures}</div>' if len(images) > 1 else figures
    if first.startswith("*") and not first.startswith("**"):
        return f'<p class="subtitle">{inline(" ".join(block))}</p>'
    if first.startswith("#"):
        level = len(first) - len(first.lstrip("#"))
        return f"<h{level}>{inline(first.lstrip('#').strip())}</h{level}>"
    if first.startswith("|"):
        return table(block)
    if first.startswith("- "):
        return f"<ul>{items(block, r'^- ')}</ul>"
    if re.match(r"\d+\. ", first):
        return f"<ol>{items(block, r'^\d+\. ')}</ol>"
    return f"<p>{inline(' '.join(line.strip() for line in block))}</p>"


def main():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    body = "\n".join(render(b) for b in blocks(lines))
    style = THEME.read_text(encoding="utf-8") + PRINT_CSS
    page = f'<!doctype html><meta charset="utf-8"><title>Rebuilding Neuron</title><style>{style}</style>{body}'
    PAGE.write_text(page, encoding="utf-8")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={PDF}", PAGE.as_uri()], check=True, capture_output=True)
    pages = len(re.findall(rb"/Type\s*/Page[^s]", PDF.read_bytes()))
    sources = [m[1] for m in re.findall(IMAGE, SOURCE.read_text(encoding="utf-8"))]
    missing = [m for m in sources if not (HERE / m).with_suffix(".png").exists()]
    print(f"{PDF.name}: {pages} pages" + (f", {len(missing)} figures missing: {', '.join(missing)}" if missing else ""))
    return 0 if pages <= 3 else 1


if __name__ == "__main__":
    sys.exit(main())
