
import os
import sys
sys.path.insert(0, os.path.abspath('../../'))

# --- Extensions & Defaults ---
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

# Theme configuration
html_theme = 'alabaster'
html_theme_options = {
    'description': 'Professional ERP system for construction businesses',
    'show_powered_by': False,
    'sidebar_width': '230px',
}

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'fastapi': ('https://fastapi.tiangolo.com', None),
    'sqlalchemy': ('https://docs.sqlalchemy.org/en/stable/', None),
}
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

# LaTeX customization for better formatting
latex_show_pagerefs = False
latex_show_urls = False

# Better handling of long names in autosummary
autosummary_filename_map = {}

project = "BuildFlow ERP System"
author = "Enis Seferi"
release = "1.0.0"
copyright = "2025, Enis Seferi"


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

        % Allow line breaks in long names
        \usepackage{seqsplit}

        % Single column index
        \makeatletter
        \renewenvironment{theindex}
          {\if@twocolumn
              \@restonecolfalse
           \else
              \@restonecoltrue
           \fi
           \setlength{\columnseprule}{0pt}
           \setlength{\columnsep}{35pt}
           \onecolumn
           \section*{\indexname}
           \markboth{\MakeUppercase\indexname}%
                    {\MakeUppercase\indexname}%
           \thispagestyle{plain}
           \setlength{\parindent}{0pt}
           \setlength{\parskip}{0pt plus 0.3pt}
           \relax
           \let\item\@idxitem}%
          {\if@restonecol\onecolumn\else\clearpage\fi}
        \makeatother

        % Better handling of long function names in tables
        \usepackage{array}
        \newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
    ''',
    'printindex': '\\footnotesize\\raggedright\\printindex',
}
