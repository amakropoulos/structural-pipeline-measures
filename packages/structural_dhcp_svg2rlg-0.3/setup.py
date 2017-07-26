#!/usr/bin/python
# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name = 'structural_dhcp_svg2rlg',
    py_modules = ['structural_dhcp_svg2rlg'],
    version = '0.3',
    author='Runar Tenfjord',
    author_email = 'runar.tenfjord@gmail.com',
    license = 'BSD',
    url = 'http://code.google.com/p/svg2rlg/',
    download_url = 'http://pypi.python.org/pypi/svg2rlg/',
    requires = ['reportlab'],
    
    classifiers=[
          'Environment :: Console',
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Multimedia :: Graphics :: Graphics Conversion',
    ],
          
    description = 'Convert SVG to Reportlab drawing',
    long_description = '''**svg2rlg** is a small utility to convert SVG to reportlab graphics.

The authors motivation was to have a more robust handling of
SVG files in the **rst2pdf** tool. Specific to be able to handle
the quirks needed to include SVG export from matplotlib.
'''
)