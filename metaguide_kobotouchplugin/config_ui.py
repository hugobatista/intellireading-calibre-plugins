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

from calibre_plugins.metaguidekobotouch.metaguiding import (
    BOLD_INTENSITIES,
    BOLD_STYLES,
    DEFAULT_BOLD_INTENSITY,
    DEFAULT_BOLD_STYLE,
    DEFAULT_FIXATION,
    FIXATION_LEVELS,
)

_BOLD_STYLE_LABELS = {
    "tag": "Real bold (font bold)",
    "shadow": "Visual bold — shadow (same layout)",
    "stroke": "Visual bold — stroke (same layout)",
}
_BOLD_STYLE_TOOLTIP = (
    "How the bold part of each word is rendered. 'Real bold' uses the font's bold face and can change "
    "line breaks and page counts on Kobo. 'Visual bold' keeps the normal font metrics and paints the "
    "emphasis with CSS, so the page count stays close to the original. Visual modes are intended for "
    "Kobo kepubs and other WebKit-based readers; EPUB files on Kobo may ignore them."
)


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

        bold_style_layout = QHBoxLayout()
        bold_style_layout.addWidget(QLabel(_("Bold style:"), self))  # type: ignore # noqa
        self.bold_style_combo = QComboBox(self)
        for style in BOLD_STYLES:
            self.bold_style_combo.addItem(_BOLD_STYLE_LABELS[style], style)
        value = device.get_pref("intellireading_bold_style")
        bold_style_index = self.bold_style_combo.findData(value)
        if bold_style_index < 0:
            bold_style_index = self.bold_style_combo.findData(DEFAULT_BOLD_STYLE)
        self.bold_style_combo.setCurrentIndex(bold_style_index)
        self.bold_style_combo.setToolTip(_BOLD_STYLE_TOOLTIP)
        bold_style_layout.addWidget(self.bold_style_combo)
        bold_style_layout.addStretch()
        layout.addLayout(bold_style_layout)

        intensity_layout = QHBoxLayout()
        intensity_layout.addWidget(QLabel(_("Bold intensity:"), self))  # type: ignore # noqa
        self.bold_intensity_combo = QComboBox(self)
        for level in BOLD_INTENSITIES:
            self.bold_intensity_combo.addItem(str(level), level)
        value = device.get_pref("intellireading_bold_intensity")
        try:
            intensity = int(value) if value is not None else DEFAULT_BOLD_INTENSITY
        except (TypeError, ValueError):
            intensity = DEFAULT_BOLD_INTENSITY
        intensity_index = self.bold_intensity_combo.findData(intensity)
        if intensity_index < 0:
            intensity_index = self.bold_intensity_combo.findData(DEFAULT_BOLD_INTENSITY)
        self.bold_intensity_combo.setCurrentIndex(intensity_index)
        self.bold_intensity_combo.setToolTip(
            _(  # type: ignore # noqa
                "How strong the visual bold effect is: 1 = subtle, 5 = strongest. "
                "Only applies to Visual bold styles."
            )
        )
        intensity_layout.addWidget(self.bold_intensity_combo)
        intensity_layout.addStretch()
        layout.addLayout(intensity_layout)

        self.bold_style_combo.currentIndexChanged.connect(self._update_bold_intensity_enabled)
        self._update_bold_intensity_enabled()

    def _update_bold_intensity_enabled(self, *_args: object) -> None:
        self.bold_intensity_combo.setEnabled(self.bold_style_combo.currentData() != "tag")

    @property
    def include_about_page(self) -> bool:
        return self.include_about_page_checkbox.isChecked()

    @property
    def fixation(self) -> int:
        return int(self.fixation_combo.currentData())

    @property
    def bold_style(self) -> str:
        return str(self.bold_style_combo.currentData())

    @property
    def bold_intensity(self) -> int:
        return int(self.bold_intensity_combo.currentData())


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
        p["intellireading_bold_style"] = self.intellireading_options.bold_style
        p["intellireading_bold_intensity"] = self.intellireading_options.bold_intensity
        return p
