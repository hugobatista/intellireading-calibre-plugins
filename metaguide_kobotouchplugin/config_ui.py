"""Configuration interface for the KoboTouch Metaguide Driver."""

__license__ = "GPL v3"
__copyright__ = "2025, Hugo Batista <intellireading at hugobatista.com>"
__docformat__ = "markdown en"

# pylint: disable=import-error
try:
    from qt.core import QCheckBox, QComboBox, QHBoxLayout, QLabel, QVBoxLayout
except ImportError:
    from PyQt5.Qt import QCheckBox, QComboBox, QHBoxLayout, QLabel, QVBoxLayout

from calibre.devices.kobo.kobotouch_config import KOBOTOUCHConfig
from calibre.gui2.device_drivers.tabbed_device_config import DeviceOptionsGroupBox

from calibre_plugins.metaguidekobotouch.metaguiding import DEFAULT_FIXATION, FIXATION_LEVELS


class IntelliReadingOptions(DeviceOptionsGroupBox):
    """IntelliReading specific options for the Kobo driver."""

    def __init__(self, parent, device):
        super().__init__(parent, device, _("IntelliReading"))  # type: ignore # noqa

        layout = QVBoxLayout(self)

        self.include_about_page_checkbox = QCheckBox(_("Add IntelliReading about/donation page"), self)  # type: ignore # noqa
        self.include_about_page_checkbox.setToolTip(
            _(  # type: ignore # noqa
                "Adds an IntelliReading about/donation page at the end of metaguided EPUBs. "
                "Disable this to keep the EPUB content unchanged."
            )
        )
        value = device.get_pref("intellireading_include_about_page")
        self.include_about_page_checkbox.setChecked(True if value is None else bool(value))
        layout.addWidget(self.include_about_page_checkbox)

        fixation_layout = QHBoxLayout()
        fixation_layout.addWidget(QLabel(_("Fixation level:"), self))  # type: ignore # noqa
        self.fixation_combo = QComboBox(self)
        for level in FIXATION_LEVELS:
            self.fixation_combo.addItem(str(level), level)
        value = device.get_pref("intellireading_fixation")
        try:
            fixation = int(value) if value is not None else DEFAULT_FIXATION
        except (TypeError, ValueError):
            fixation = DEFAULT_FIXATION
        fixation_index = self.fixation_combo.findData(fixation)
        if fixation_index < 0:
            fixation_index = self.fixation_combo.findData(DEFAULT_FIXATION)
        self.fixation_combo.setCurrentIndex(fixation_index)
        self.fixation_combo.setToolTip(
            _("How much of each word is bolded. 1 = least bold, 5 = most bold. Default: 3.")  # type: ignore # noqa
        )
        fixation_layout.addWidget(self.fixation_combo)
        fixation_layout.addStretch()
        layout.addLayout(fixation_layout)

    @property
    def include_about_page(self) -> bool:
        return self.include_about_page_checkbox.isChecked()

    @property
    def fixation(self) -> int:
        return int(self.fixation_combo.currentData())


class IntelliReadingKoboTouchConfig(KOBOTOUCHConfig):
    """Kobo driver configuration with IntelliReading options."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.intellireading_options = IntelliReadingOptions(self, self.device)
        self.tab1.l.insertWidget(self.tab1.l.count() - 1, self.intellireading_options)
        self.tab1.addDeviceWidget(self.intellireading_options)

    def commit(self):
        p = super().commit()
        p["intellireading_include_about_page"] = self.intellireading_options.include_about_page
        p["intellireading_fixation"] = self.intellireading_options.fixation
        return p
