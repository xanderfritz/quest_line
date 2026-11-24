# sphinx config for the quest_line project

import os
import sys
import django

sys.path.insert(0, os.path.abspath(".."))
os.environ['DJANGO_SETTINGS_MODULE'] = 'quest_line.settings'
os.environ.setdefault('DB_ENGINE', 'sqlite')
django.setup()

project = 'quest_line'
copyright = '2026, Xander Fritz'
author = 'Xander Fritz'

version = '1.0.0'
release = '1.0.0'

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon"
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

language = 'en'

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
