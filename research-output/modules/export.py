### Script that exportes the research output in tabular format from bibtexs ###

import sys

sys.path.append("./modules")

from modules.utilities import *

import pybtex  # official documentation https://docs.pybtex.org/
import pybtex.database.input.bibtex
from pybtex.plugin import find_plugin

from weasyprint import HTML # HTML to PDF export

import subprocess # run pandoc command

"""
Research output BibTeX folder has the following hierarchy:

- research group
	- researcher
		- reseacher_full_output.bib  

"""

chicago_16_bst_filepath = os.path.join("mappings", "chicago-author-date-16.bst")

orpheus_instituut_csl_filepath = os.path.join("mappings","orpheus-author-date-2.8.csl")

research_output_directory = os.path.join("data")

html_template_filepath = os.path.join("mappings","template.html")

csl_style_filepath = os.path.join("mappings","style.css")

def html_to_pdf(html_path, pdf_path):

    print("Rendering PDF with WeasyPrint:", pdf_path)
    HTML(filename=str(html_path)).write_pdf(str(pdf_path))
    print("Wrote PDF to", pdf_path)


def research_cluster_export(
    cluster_directory,csl_style_filepath=orpheus_instituut_csl_filepath, css_style_filepath=csl_style_filepath
): 
	print(f"Current cluster: {os.path.basename(cluster_directory).replace("_"," ")}")
	print("Merging researchers' bibliographies...")
	# Generate a joint BibTex for research cluster
	merged_bib_filename = os.path.join("export", f"{os.path.basename(cluster_directory)}.bib")
	merged_bib_file = open(merged_bib_filename,"w",encoding="utf-8")
	for researcher in os.scandir(cluster_directory):
		researcher_full_output_file = open(f"{researcher.path}/{researcher.name}_full_output.bib","r",encoding="utf-8")
		# Append to merged bib file
		merged_bib_file.write(researcher_full_output_file.read())
		merged_bib_file.write("\n\n")
		researcher_full_output_file.close()

	merged_bib_file.close()

	# Generate Markdown
	print("Generating Markdown bibliography template ...")
	merged_md_filename = os.path.join("export", f"{os.path.basename(cluster_directory)}.md")
	merged_md_file = open(merged_md_filename,"w",encoding="utf-8")
	title = os.path.basename(cluster_directory.replace("_"," "))
	md = []
	md.append("---")
	md.append(f"title: \"{title}\"")
	md.append(f"bibliography: {merged_bib_filename}")
	md.append('nocite: "@*"')
	md.append("---")
	md.append("")
	#md.append(f"# {title}")
	md.append("<!-- The bibliography will be rendered below by pandoc + citeproc -->")
	md.append("")
	md_text = "\n".join(md)
	merged_md_file.write(md_text)
	merged_md_file.close()



	# Use pandoc and CSL style to generate PDF and HTML

	merged_html_filename = os.path.join("export", f"{os.path.basename(cluster_directory)}.html")
	merged_pdf_filename = os.path.join("export", f"{os.path.basename(cluster_directory)}.pdf")

	cmd = [
	    "pandoc",
	    str(merged_md_filename),
	    "--standalone",
	    "--from", "markdown",
	    "--to", "html5",
	    "--output", str(merged_html_filename),
	    "--citeproc",
	    "--csl", str(csl_style_filepath),
	    "--css", str(css_style_filepath)
	]

	print(f"Parsing into HTML using pandoc... ")
	subprocess.run(cmd,check=True)

	# Export to PDF
	print("Exporting to PDF...")
	html_to_pdf(merged_html_filename, merged_pdf_filename)




