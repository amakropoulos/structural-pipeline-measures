svg2rlg is a tool to convert from SVG to reportlab graphics objects.

License: BSD

Note that the reportlab rendering to image files does not correctly handle
the 'fillOpacity' attribute and also the filling rules is not handled. 
Some tests in the test suite will therfore fail as an image, but it will render
correctly in a PDF.

The test suite is not included, but can be downloaded and put in the 'test-suite'
folder. If wxpython is installed the file 'svg2rlg_render_test.py' will render
the svg and show the corresponding expected png image.

The SVG test suite can be download at:
  
  http://www.w3.org/Graphics/SVG/Test/20061213/archives/W3C_SVG_11_FullTestSuite.tar.gz


Runar Tenfjord <runar.tenfjord@gmail.com>