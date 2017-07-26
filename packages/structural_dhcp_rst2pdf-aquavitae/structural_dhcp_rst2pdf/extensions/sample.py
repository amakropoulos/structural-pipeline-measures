print('''
This is a sample structural_dhcp_rst2pdf extension.

Because it is named 'sample.py' you can get structural_dhcp_rst2pdf to import it by
putting '-e sample' on the structural_dhcp_rst2pdf command line.

An extension is called after the command-line is parsed, and can
monkey-patch any necessary changes into structural_dhcp_rst2pdf.

An extension can live either in the extensions subdirectory, or
anywhere on the python path.
''')

def install(createpdf, options):
    ''' This function is called with an object with the createpdf
        module globals as attributes, and with the options from
        the command line parser.  This function does not have
        to exist, but must have the correct call signature if
        it does.
    '''
