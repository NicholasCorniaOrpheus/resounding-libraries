#!/usr/bin/env python3
"""
generate_bib_report.py

Create an HTML (and PDF) report of all entries across one or more BibTeX files,
formatted with a Chicago notes & bibliography CSL (suitable for Chicago 16th-edition rules),
using pandoc + --citeproc to produce the bibliography, then convert HTML -> PDF using WeasyPrint.

Usage (example):
  python generate_bib_report.py \
    --bib inputs/*.bib \
    --title "Institution Publications 2025" \
    --author "Research Office" \
    --output report.pdf

Requirements:
  - pandoc available on PATH
  - Python packages in requirements.txt
  - WeasyPrint system deps (cairo, pango, gdk-pixbuf) installed for PDF output

Author: (generated)
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
import os
from pathlib import Path
import urllib.request

DEFAULT_CSL_URL = "https://raw.githubusercontent.com/citation-style-language/styles/master/chicago-fullnote-bibliography.csl"

TEMPLATE_NAME = "template.html"

def check_program(name):
    if shutil.which(name) is None:
        print(f"ERROR: Required program '{name}' not found on PATH. Please install it.", file=sys.stderr)
        return False
    return True

def download_csl(csl_path: Path, url=DEFAULT_CSL_URL):
    print(f"Downloading default CSL from {url} -> {csl_path}")
    urllib.request.urlretrieve(url, str(csl_path))

def merge_bibs(bib_paths, out_path: Path):
    print("Merging BibTeX files into:", out_path)
    with out_path.open("w", encoding="utf-8") as w:
        for p in bib_paths:
            print("  adding", p)
            with open(p, "r", encoding="utf-8") as r:
                w.write(r.read())
                w.write("\n\n")

def make_markdown_md(title, author, institution, merged_bib_path: Path, md_path: Path):
    md = []
    md.append("---")
    md.append(f"title: \"{title}\"")
    if author:
        md.append(f"author: \"{author}\"")
    md.append(f"bibliography: {merged_bib_path.name}")
    md.append('nocite: "@*"')
    md.append("---")
    md.append("")
    md.append(f"# {title}")
    if institution:
        md.append(f"**{institution}**")
        md.append("")
    md.append("<!-- The bibliography will be rendered below by pandoc + citeproc -->")
    md.append("")
    md_text = "\n".join(md)
    md_path.write_text(md_text, encoding="utf-8")
    print("Wrote temporary markdown to", md_path)

def run_pandoc(md_path: Path, template_path: Path, csl_path: Path, out_html: Path, extra_css=None):
    cmd = [
        "pandoc",
        str(md_path),
        "--standalone",
        "--from", "markdown",
        "--to", "html5",
        "--output", str(out_html),
        "--template", str(template_path),
        "--citeproc",
        "--csl", str(csl_path)
    ]
    if extra_css:
        # Pandoc will embed link rel=stylesheet in head if we pass --css, but we use a template that already provides styles.
        cmd += ["--css", str(extra_css)]
    print("Running pandoc:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("Pandoc produced HTML at", out_html)

def html_to_pdf(html_path: Path, pdf_path: Path):
    try:
        from weasyprint import HTML
    except Exception as e:
        print("ERROR: WeasyPrint is required for HTML -> PDF conversion.", file=sys.stderr)
        print("Install with: pip install weasyprint", file=sys.stderr)
        raise

    print("Rendering PDF with WeasyPrint:", pdf_path)
    HTML(filename=str(html_path)).write_pdf(str(pdf_path))
    print("Wrote PDF to", pdf_path)

def main():
    parser = argparse.ArgumentParser(description="Generate bibliography report (Chicago) from BibTeX -> HTML -> PDF")
    parser.add_argument("--bib", "-b", nargs="+", required=True, help="One or more BibTeX files (globbing allowed by your shell)")
    parser.add_argument("--csl", help="Path to a CSL file to use (if omitted, the script downloads chicago-fullnote-bibliography.csl)")
    parser.add_argument("--title", default="Publications", help="Document title")
    parser.add_argument("--author", default="", help="Author/maintainer for the report")
    parser.add_argument("--institution", default="", help="Institution name to display under the title")
    parser.add_argument("--output", "-o", default="report.pdf", help="Output PDF file")
    parser.add_argument("--no-pdf", action="store_true", help="Produce only HTML (don't convert to PDF)")
    parser.add_argument("--template", help="Optional custom pandoc template (HTML). If omitted, the embedded template is used.")
    args = parser.parse_args()

    if not check_program("pandoc"):
        sys.exit(1)

    bib_paths = []
    for p in args.bib:
        matches = list(Path().glob(p)) if ("*" in p or "?" in p or "[" in p) else [Path(p)]
        if not matches:
            print(f"WARNING: No files matched pattern {p}", file=sys.stderr)
        for m in matches:
            if not m.exists():
                print(f"ERROR: Bib file {m} does not exist", file=sys.stderr)
                sys.exit(1)
            bib_paths.append(m)

    if not bib_paths:
        print("ERROR: No BibTeX files provided", file=sys.stderr)
        sys.exit(1)

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        merged_bib = td / "merged.bib"
        merge_bibs(bib_paths, merged_bib)

        # Ensure CSL is present
        if args.csl:
            csl_path = Path(args.csl)
            if not csl_path.exists():
                print(f"ERROR: CSL file {csl_path} not found", file=sys.stderr)
                sys.exit(1)
        else:
            csl_path = td / "chicago-fullnote-bibliography.csl"
            download_csl(csl_path)

        # Prepare template
        if args.template:
            template_path = Path(args.template)
            if not template_path.exists():
                print(f"ERROR: Template {template_path} not found", file=sys.stderr)
                sys.exit(1)
        else:
            # write our bundled template to tempdir
            here = Path(__file__).parent
            template_text = PACKAGE_TEMPLATE_HTML
            template_path = td / TEMPLATE_NAME
            template_path.write_text(template_text, encoding="utf-8")
            # also write a small CSS file if you want external
            # not necessary; template contains style
        # Create md file
        md_path = td / "report.md"
        make_markdown_md(args.title, args.author, args.institution, merged_bib, md_path)

        # copy merged_bib to same dir as md so pandoc's relative bibliographies work
        # The md references merged_bib by filename (not absolute), so ensure it's in same folder
        # merged_bib already in td alongside md.
        out_html = Path(args.output).with_suffix(".html")
        run_pandoc(md_path, template_path, csl_path, out_html)

        if args.no_pdf:
            print("No-PDF requested; leaving HTML at", out_html)
            return

        out_pdf = Path(args.output)
        try:
            html_to_pdf(out_html, out_pdf)
        except Exception as e:
            print("PDF conversion failed:", e, file=sys.stderr)
            print("You can still open the HTML:", out_html)
            sys.exit(1)

# Embedded template HTML (pandoc template). It imports Sofia Sans from Google Fonts.
PACKAGE_TEMPLATE_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>$title$</title>
<style>
/* Load Sofia Sans from Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Sofia+Sans&display=swap');

:root{
  --body-font: "Sofia Sans", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
  --max-width: 900px;
  --accent: #0a3d62;
  --muted: #555;
}

body{
  font-family: var(--body-font);
  color: #222;
  line-height: 1.45;
  margin: 0;
  padding: 2rem;
  display: flex;
  justify-content: center;
  background: #fff;
}

.container{
  width: 100%;
  max-width: var(--max-width);
}

h1{
  color: var(--accent);
  font-size: 1.9rem;
  margin-bottom: 0.2rem;
}

.header-meta{
  color: var(--muted);
  margin-bottom: 1.4rem;
}

#content{
  margin-top: 1rem;
}

/* Bibliography styling - pandoc will output <div id="refs"><div class="csl-bib-body"> ... */
#refs {
  margin-top: 1.2rem;
  font-size: 0.95rem;
}

.csl-entry {
  margin: 0.6rem 0;
  text-indent: -1.2em;
  padding-left: 1.4em;
}

/* Ensure links are visible */
a { color: #0b63a5; text-decoration: none; }
a:hover { text-decoration: underline; }

@media print {
  body { padding: 1cm; }
}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>$title$</h1>
    <div class="header-meta">
      $if(author)$$author$$endif$
      $if(institution)$<div>$institution$</div>$endif$
    </div>
  </header>

  <main id="content">
$body$
  </main>

</div>
</body>
</html>
"""

if __name__ == "__main__":
    main()