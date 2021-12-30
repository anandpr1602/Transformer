# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
from __future__ import unicode_literals

import os


# -- Project information -----------------------------------------------------

project = 'Transformer'
copyright = '2021, Jonathan M Skelton'
author = 'Jonathan M Skelton'
source_suffix = '.rst'
master_doc = 'index'
pygments_style = 'trac'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinxcontrib.apidoc',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.coverage',
    'sphinx.ext.doctest',
    'sphinx.ext.extlinks',
    'sphinx.ext.ifconfig',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'pbr.sphinxext',
	'rinoh.frontend.sphinx',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

extlinks = {
    'issue': ('https://github.com/JMSkelton/Transformer/issues/%s', '#'),
    'pr': ('https://github.com/JMSkelton/Transformer/pulls/%s', 'PR #'),
}

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

# on_rtd is whether we are on readthedocs.org
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
if not on_rtd:  # only set the theme if we're building docs locally
    html_theme = 'sphinx_rtd_theme'

html_use_smartypants = True
html_last_updated_fmt = '%b %d, %Y'
html_split_index = False
html_sidebars = {
   '**': ['searchbox.html', 'globaltoc.html', 'sourcelink.html'],
}
html_short_title = '%s' % (project)

apidoc_module_dir = '../../Transformer'
apidoc_output_dir = '.'
apidoc_excluded_paths = ['tests']
apidoc_separate_modules = True

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Napoleon settings 
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True
napoleon_custom_sections = [("Keyword arguments:", "params_style"), ("Return value:", "params_style"), ("Notes:", "params_style")]

# Display todos by setting to True
todo_include_todos = True

rinoh_documents = [dict(doc='index', target='Transformer API Manual', title='Transformer API Manual')]

latex_elements = {
    'papersize': 'A4',
    'pointsize': '10pt',
    'preamble': '',
    'figure_align': 'htbp'}
