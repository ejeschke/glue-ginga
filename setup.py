#!/usr/bin/env python

from __future__ import print_function

from setuptools import setup, find_packages

entry_points = """
[glue.plugins]
ginga=glue_ginga:setup
"""

try:
    import pypandoc
    LONG_DESCRIPTION = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
    with open('README.md') as infile:
        LONG_DESCRIPTION = infile.read()

with open('glue_ginga/version.py') as infile:
    exec(infile.read())

setup(name='glue-ginga',
      version=__version__,
      description='Ginga viewer plugin for glue',
      long_description=LONG_DESCRIPTION,
      url="https://github.com/ejeschke/glue-ginga",
      author='Eric Jeschke, Tom Robitaille',
      author_email='eric@naoj.org, thomas.robitaille@gmail.com',
      packages = find_packages(),
      package_data={},
      entry_points=entry_points,
      install_requires=['glueviz>=0.9.0',
                        'ginga']
     )
