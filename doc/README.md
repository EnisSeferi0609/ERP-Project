# BuildFlow ERP Documentation

This directory contains Sphinx documentation for the BuildFlow ERP system.

## Building Documentation

### Prerequisites

Install Sphinx and dependencies:

```bash
pip install sphinx sphinx-rtd-theme
```

### Build HTML Documentation

```bash
cd doc
make html
```

The generated HTML documentation will be in `build/html/index.html`.

### Build PDF Documentation

```bash
cd doc
make latexpdf
```

Requires LaTeX installation (e.g., TeX Live on Linux/macOS, MiKTeX on Windows).

### Clean Build Files

```bash
cd doc
make clean
```

## Documentation Structure

- `source/index.rst` - Main documentation index
- `source/conf.py` - Sphinx configuration
- `source/_autosummary/` - Auto-generated API documentation
- `build/` - Generated documentation (not tracked in git)

The documentation automatically generates API reference from docstrings in the Python code.