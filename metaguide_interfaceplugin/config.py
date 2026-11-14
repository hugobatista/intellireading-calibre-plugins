"""
Configuration for the Epub Metaguider interface plugin.
"""

__license__ = "GPL v3"
__copyright__ = "2025, Hugo Batista <intellireading at hugobatista.com>"

from calibre.utils.config import JSONConfig

from calibre_plugins.metaguideinterface.metaguiding import DEFAULT_FIXATION

# This is where all preferences for this plugin will be stored
# Remember that this name (metaguideinterface) must be unique
# as calibre creates global config files using it
prefs = JSONConfig("plugins/metaguideinterface")

# Set defaults
prefs.defaults["default_action"] = "epub"  # can be 'epub' or 'kepub'
prefs.defaults["include_about_page"] = True
prefs.defaults["fixation"] = DEFAULT_FIXATION
