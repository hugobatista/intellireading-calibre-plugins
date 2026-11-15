"""Configuration for exporting epubmg files."""

__license__ = "GPL v3"
__copyright__ = "2025, Hugo Batista <intellireading at hugobatista.com>"
__docformat__ = "markdown en"

# pylint: disable=import-error
from calibre.ebooks.conversion.config import OPTIONS
from calibre.gui2.convert import Widget
from calibre.gui2.convert.epub_output import PluginWidget as EPUBPluginWidget
from calibre.gui2.convert.epub_output_ui import Ui_Form as EPUBUIForm

from calibre_plugins.metaguideoutput import common
from calibre_plugins.metaguideoutput.metaguiding import BOLD_INTENSITIES, BOLD_STYLES, FIXATION_LEVELS


class PluginWidget(EPUBPluginWidget, EPUBUIForm):
    """The plugin configuration widget for a epubmg output plugin."""

    # pylint:disable=undefined-variable
    TITLE = "Epub Output (metaguided)"
    HELP = _("Options specific to Epub output (metaguided)")  # type: ignore # noqa
    COMMIT_NAME = "epubmg_output"

    # A near copy of calibre.gui2.convert.epub_output.PluginWidget#__init__
    # If something seems wrong, start by checking for changes there.
    # We copy that instead of calling super().__init__() because the super __init__
    # calls Widget.__init__() with ePub options and there's no easy way to add and link
    # new UI elements once that's been done.
    def __init__(self, parent, get_option, get_help, db=None, book_id=None):
        """Initialize the epubmg output configuration widget."""
        common.log.debug("Initalizing epubmg output plugin widget")

        Widget.__init__(
            self,
            parent,
            OPTIONS["output"].get("epub", tuple())
            + (
                "epubmg_enable_metaguiding",
                "epubmg_include_about_page",
                "epubmg_fixation",
                "epubmg_bold_style",
                "epubmg_bold_intensity",
            ),
        )
        self.opt_no_svg_cover.toggle()
        self.opt_no_svg_cover.toggle()
        _ev = get_option("epub_version")
        self.opt_epub_version.addItems(list(_ev.option.choices))
        self.db, self.book_id = db, book_id
        self.initialize_options(get_option, get_help, db, book_id)
        self._update_bold_intensity_enabled()

    def setupUi(self, Form):  # noqa: N802, N803
        """Set up the plugin widget UI."""
        # pylint:disable=undefined-variable
        # pylint:disable=attribute-defined-outside-init
        common.log.debug("Setting up epubmg output plugin widget")
        super(PluginWidget, self).setupUi(Form)

        from PyQt5 import QtWidgets  # pylint: disable=import-error # type: ignore
        from PyQt5 import QtCore  # pylint: disable=import-error # type: ignore

        _rows = self.gridLayout.rowCount() - 1

        spacer = self.gridLayout.itemAtPosition(_rows, 0)
        self.gridLayout.removeItem(spacer)

        self.opt_additional_conversion_options = QtWidgets.QLabel(
            _("Additional Conversion options") + ":"  # type: ignore # noqa
        )
        self.gridLayout.addWidget(self.opt_additional_conversion_options, _rows, 0, 1, 1)

        # epubmg_enable_metaguiding
        self.opt_epubmg_enable_metaguiding = QtWidgets.QCheckBox(Form)
        self.opt_epubmg_enable_metaguiding.setObjectName("opt_epubmg_enable_metaguiding")
        self.opt_epubmg_enable_metaguiding.setText(_("Enable metaguiding"))  # type: ignore # noqa
        self.gridLayout.addWidget(self.opt_epubmg_enable_metaguiding, _rows, 1, 1, 1)

        _rows += 1

        # epubmg_include_about_page
        self.opt_epubmg_include_about_page = QtWidgets.QCheckBox(Form)
        self.opt_epubmg_include_about_page.setObjectName("opt_epubmg_include_about_page")
        self.opt_epubmg_include_about_page.setText(_("Add IntelliReading about/donation page"))  # type: ignore # noqa
        self.gridLayout.addWidget(self.opt_epubmg_include_about_page, _rows, 1, 1, 1)

        self.opt_epubmg_enable_metaguiding.toggled.connect(self.opt_epubmg_include_about_page.setEnabled)
        self.opt_epubmg_include_about_page.setEnabled(self.opt_epubmg_enable_metaguiding.isChecked())

        _rows += 1

        # epubmg_fixation
        self.opt_epubmg_fixation_label = QtWidgets.QLabel(_("Fixation level") + ":", Form)  # type: ignore # noqa
        self.gridLayout.addWidget(self.opt_epubmg_fixation_label, _rows, 0, 1, 1)

        self.opt_epubmg_fixation = QtWidgets.QComboBox(Form)
        self.opt_epubmg_fixation.setObjectName("opt_epubmg_fixation")
        self.opt_epubmg_fixation.addItems([str(level) for level in FIXATION_LEVELS])
        self.opt_epubmg_fixation.setToolTip(
            _("How much of each word is bolded: 1 = least bold, 5 = most bold. Default: 3.")  # type: ignore # noqa
        )
        self.gridLayout.addWidget(self.opt_epubmg_fixation, _rows, 1, 1, 1)

        self.opt_epubmg_enable_metaguiding.toggled.connect(self.opt_epubmg_fixation_label.setEnabled)
        self.opt_epubmg_enable_metaguiding.toggled.connect(self.opt_epubmg_fixation.setEnabled)
        self.opt_epubmg_fixation_label.setEnabled(self.opt_epubmg_enable_metaguiding.isChecked())
        self.opt_epubmg_fixation.setEnabled(self.opt_epubmg_enable_metaguiding.isChecked())

        _rows += 1

        # epubmg_bold_style
        self.opt_epubmg_bold_style_label = QtWidgets.QLabel(_("Bold style") + ":", Form)  # type: ignore # noqa
        self.gridLayout.addWidget(self.opt_epubmg_bold_style_label, _rows, 0, 1, 1)

        self.opt_epubmg_bold_style = QtWidgets.QComboBox(Form)
        self.opt_epubmg_bold_style.setObjectName("opt_epubmg_bold_style")
        self.opt_epubmg_bold_style.addItems(list(BOLD_STYLES))
        self.opt_epubmg_bold_style.setToolTip(
            _(  # type: ignore # noqa
                "How to render the bold emphasis. 'tag' uses the real bold font; "
                "'shadow' and 'stroke' keep the original font metrics and avoid page count changes "
                "on Kobo kepubs. Default: tag."
            )
        )
        self.gridLayout.addWidget(self.opt_epubmg_bold_style, _rows, 1, 1, 1)

        self.opt_epubmg_enable_metaguiding.toggled.connect(self.opt_epubmg_bold_style_label.setEnabled)
        self.opt_epubmg_enable_metaguiding.toggled.connect(self.opt_epubmg_bold_style.setEnabled)
        self.opt_epubmg_bold_style_label.setEnabled(self.opt_epubmg_enable_metaguiding.isChecked())
        self.opt_epubmg_bold_style.setEnabled(self.opt_epubmg_enable_metaguiding.isChecked())

        _rows += 1

        # epubmg_bold_intensity
        self.opt_epubmg_bold_intensity_label = QtWidgets.QLabel(_("Bold intensity") + ":", Form)  # type: ignore # noqa
        self.gridLayout.addWidget(self.opt_epubmg_bold_intensity_label, _rows, 0, 1, 1)

        self.opt_epubmg_bold_intensity = QtWidgets.QComboBox(Form)
        self.opt_epubmg_bold_intensity.setObjectName("opt_epubmg_bold_intensity")
        self.opt_epubmg_bold_intensity.addItems([str(level) for level in BOLD_INTENSITIES])
        self.opt_epubmg_bold_intensity.setToolTip(
            _(  # type: ignore # noqa
                "How strong the visual bold effect is: 1 = subtle, 5 = strongest. "
                "Only applies to the 'shadow' and 'stroke' styles. Default: 3."
            )
        )
        self.gridLayout.addWidget(self.opt_epubmg_bold_intensity, _rows, 1, 1, 1)

        self.opt_epubmg_enable_metaguiding.toggled.connect(self._update_bold_intensity_enabled)
        self.opt_epubmg_bold_style.currentTextChanged.connect(self._update_bold_intensity_enabled)
        self._update_bold_intensity_enabled()

        _rows += 1

        self.gridLayout.addItem(spacer, _rows, 0, 1, 1)

        # Copy from calibre.gui2.convert.epub_output_ui.Ui_Form to make the
        # new additions work
        QtCore.QMetaObject.connectSlotsByName(Form)

    def _update_bold_intensity_enabled(self, *_args: object) -> None:
        enabled = (
            self.opt_epubmg_enable_metaguiding.isChecked()
            and self.opt_epubmg_bold_style.currentText() != "tag"
        )
        self.opt_epubmg_bold_intensity_label.setEnabled(enabled)
        self.opt_epubmg_bold_intensity.setEnabled(enabled)
