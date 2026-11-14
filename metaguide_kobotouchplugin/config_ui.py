"""Configuration interface for the KoboTouch Metaguide Driver."""

__license__ = "GPL v3"
__copyright__ = "2025, Hugo Batista <intellireading at hugobatista.com>"
__docformat__ = "markdown en"

# pylint: disable=import-error
try:
    from qt.core import QCheckBox, QVBoxLayout
except ImportError:
    from PyQt5.Qt import QCheckBox, QVBoxLayout

from calibre.devices.kobo.kobotouch_config import KOBOTOUCHConfig
from calibre.gui2.device_drivers.tabbed_device_config import DeviceOptionsGroupBox


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

    @property
    def include_about_page(self) -> bool:
        return self.include_about_page_checkbox.isChecked()


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
        return p
