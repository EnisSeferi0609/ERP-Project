
import os
import sys
sys.path.insert(0, os.path.abspath('../../'))

# --- Extensions & Defaults ---
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
]
autosummary_generate = True

# Docstring-Stil (Google/Numpy) + Typen
napoleon_google_docstring = True
napoleon_numpy_docstring = True
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

project = "ERP-Projekt"
author = "Enis Seferi"
release = "0.1"


latex_engine = 'xelatex'
latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '11pt',
    'classoptions': ',openany,oneside',
    'preamble': r'''
        \usepackage{titlesec}
        \titleformat{\section}{\Large\bfseries}{\thesection}{1em}{}
        \titleformat{\subsection}{\large\bfseries}{\thesubsection}{1em}{}
        \usepackage{enumitem}
        \setlist{nosep}
        \usepackage{parskip}
    ''',
}
