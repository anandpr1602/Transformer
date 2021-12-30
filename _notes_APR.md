## Styling & edits

 - used [Python docstring generator](https://github.com/NilsJPWerner/autoDocstring) - installed as a VS Code extension to create [Numpy docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html#example-numpy) (other popular styles - [Google](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) or Sphinx).
 - updated module docstring with some Sphinx/RST identifiers.
 - added `.. note:` docstring keyword.
 - added cross-references to `:func:`, `:mod:` and `:class:` objects.
 - changed `raise` a general `Exception` to raising an `AssertionError` for typechecks.
 - `mixedCaseFont` or `CamelToe` fonttypes are reserved usually for Classes. Discouraged for functions, args, and variables.
 - is `warnings` module required if only to raise a `RuntimeWarning`?
 - `maxNumProcesses`, `progressBar` in `QueueMapFunction` were not `kwargs`. Fixed them with default value assignment.
 - removed `__init__` for `AccumulatorBase` and `MapperBase` classes.

## Installation

 - added empty `requirements.txt` (good practice to assign specific package versions, unless unit-tested).
 - added `requirements_dev.txt` for package developers - see below for what has been added.
 - "... works in Python >= 2.7 and Python 3..." generally avoided unless tested with specific dev environments. Suggest using [Tox](https://pypi.org/project/tox/); [example](https://tox.wiki/en/latest/examples.html).

 ## Semantic Versioning using PBR

  - added [PBR version tracking](https://pypi.org/project/pbr/).
  - added `setup.py` and `setup.cfg` (can run `python -m setup sdist`).
  - can modify `setup.cfg` in future to add additional tasks (e.g., `pip install transformer`, uploading `Transformer` to PyPI, running TOX tests, unittesting, etc.)

## Documentation

 - Implemented [Sphinx autodoc](https://www.sphinx-doc.org/en/master/) feature...
 - Made HTML and PDFs (PDFs using [rinohtype](https://www.mos6581.org/rinohtype/master/#) pacakge).
 - HTML entry point --> "./Transformer/blob/master/docs/build/html/index.html".
 - Navigate to `Transformer.Utilities.MultiprocessingHelper` to see a proper example of auto-doc-ing.
 - PDF --> "./Transformer/docs/build/pdf/Transformer API Manual.pdf".
 - Only `Transformer.Utilities.MultiprocessingHelper` populated correctly as of noww.
