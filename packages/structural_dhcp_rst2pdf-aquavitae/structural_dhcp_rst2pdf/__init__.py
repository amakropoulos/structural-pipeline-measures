# See LICENSE.txt for licensing terms
try:
    import pkg_resources
    try:
        version = pkg_resources.get_distribution('structural_dhcp_rst2pdf').version
    except pkg_resources.ResolutionError:
        version = None
except ImportError:
    version = None
