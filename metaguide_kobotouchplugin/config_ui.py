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
from calibre.gui2.device_drivers.tabbed_device_config import (
    DeviceConfigTab,
    DeviceOptionsGroupBox,
)

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
_PAGE_FIX_TOOLTIP = (
    "EXPERIMENTAL. Back up your Kobo before enabling this option: the driver writes directly to the "
    "Kobo database. Before the device imports the book, pre-creates the Kobo database rows so the "
    "Kobo uses IntelliReading's clean word counts. This avoids the inflated page count caused by "
    "inline bold tags, without reconnecting the device. Only applies to new KEPUB uploads on the "
    "main memory. Existing books, plain EPUB uploads, and books on a memory card are not modified. "
    "Default: off."
)


class MetaguidingOptions(DeviceOptionsGroupBox):
    """Metaguiding options for the Kobo driver."""

    def __init__(self, parent, device):
        super().__init__(parent, device, _("Metaguiding"))  # type: ignore # noqa

        layout = QVBoxLayout(self)

        self.enable_metaguiding_checkbox = QCheckBox(_("Enable metaguiding"), self)  # type: ignore # noqa
        self.enable_metaguiding_checkbox.setToolTip(
            _(  # type: ignore # noqa
                "When disabled, books are sent without IntelliReading metaguiding. The Kobo "
                "driver may still convert EPUB files to KEPUB according to its own settings. "
                "The experimental page-count fix is also disabled."
            )
        )
        value = device.get_pref("intellireading_enable_metaguiding")
        self.enable_metaguiding_checkbox.setChecked(True if value is None else bool(value))
        layout.addWidget(self.enable_metaguiding_checkbox)

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
        self.fixation_label = QLabel(_("Fixation level:"), self)  # type: ignore # noqa
        fixation_layout.addWidget(self.fixation_label)
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
        self.bold_style_label = QLabel(_("Bold style:"), self)  # type: ignore # noqa
        bold_style_layout.addWidget(self.bold_style_label)
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
        self.bold_intensity_label = QLabel(_("Bold intensity:"), self)  # type: ignore # noqa
        intensity_layout.addWidget(self.bold_intensity_label)
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

        self.enable_metaguiding_checkbox.toggled.connect(self._update_metaguiding_enabled)
        self.bold_style_combo.currentIndexChanged.connect(self._update_metaguiding_enabled)
        self._update_metaguiding_enabled()

    def _update_metaguiding_enabled(self, *_args: object) -> None:
        enabled = self.enable_metaguiding_checkbox.isChecked()
        for widget in (
            self.include_about_page_checkbox,
            self.fixation_label,
            self.fixation_combo,
            self.bold_style_label,
            self.bold_style_combo,
        ):
            widget.setEnabled(enabled)
        self._update_bold_intensity_enabled()

    def _update_bold_intensity_enabled(self, *_args: object) -> None:
        enabled = (
            self.enable_metaguiding_checkbox.isChecked()
            and self.bold_style_combo.currentData() != "tag"
        )
        self.bold_intensity_label.setEnabled(enabled)
        self.bold_intensity_combo.setEnabled(enabled)

    @property
    def enable_metaguiding(self) -> bool:
        return self.enable_metaguiding_checkbox.isChecked()

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


class PageCountOptions(DeviceOptionsGroupBox):
    """Experimental Kobo page-count correction options."""

    def __init__(self, parent, device):
        super().__init__(parent, device, _("Page count (experimental)"))  # type: ignore # noqa

        layout = QVBoxLayout(self)
        self.enable_page_fix_checkbox = QCheckBox(
            _("Experimental: correct Kobo page counts for new books"), self  # type: ignore # noqa
        )
        self.enable_page_fix_checkbox.setToolTip(_PAGE_FIX_TOOLTIP)
        value = device.get_pref("intellireading_enable_page_fix")
        self.enable_page_fix_checkbox.setChecked(False if value is None else bool(value))
        layout.addWidget(self.enable_page_fix_checkbox)

        self.backup_label = QLabel(
            _(  # type: ignore # noqa
                "<b>Back up your Kobo before enabling this option.</b> The driver writes "
                "directly to the Kobo database."
            ),
            self,
        )
        self.backup_label.setWordWrap(True)
        layout.addWidget(self.backup_label)

        self.warning_label = QLabel(
            _(  # type: ignore # noqa
                "Experimental feature. Only new KEPUB uploads on the main memory are affected. "
                "If a book is already on the device, delete it and send it again to rebuild its "
                "page counts. Plain EPUB uploads and books on a memory card are not modified."
            ),
            self,
        )
        self.warning_label.setWordWrap(True)
        layout.addWidget(self.warning_label)

    @property
    def enable_page_fix(self) -> bool:
        return self.enable_page_fix_checkbox.isChecked()


class IntelliReadingTab(DeviceConfigTab):
    """Dedicated IntelliReading tab for the Kobo driver options."""

    def __init__(self, parent, device):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self.metaguiding_options = MetaguidingOptions(self, device)
        self.page_count_options = PageCountOptions(self, device)
        layout.addWidget(self.metaguiding_options)
        layout.addWidget(self.page_count_options)
        self.addDeviceWidget(self.metaguiding_options)
        self.addDeviceWidget(self.page_count_options)
        layout.addStretch(1)

        self.metaguiding_options.enable_metaguiding_checkbox.toggled.connect(
            self._update_page_fix_enabled
        )
        self._update_page_fix_enabled()

    def _update_page_fix_enabled(self, *_args: object) -> None:
        enabled = self.metaguiding_options.enable_metaguiding_checkbox.isChecked()
        self.page_count_options.setEnabled(enabled)


class IntelliReadingKoboTouchConfig(KOBOTOUCHConfig):
    """Kobo driver configuration with a dedicated IntelliReading tab."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.intellireading_tab = IntelliReadingTab(self, self.device)
        self.addDeviceTab(self.intellireading_tab, _("IntelliReading"))  # type: ignore # noqa

    def commit(self):
        p = super().commit()
        metaguiding = self.intellireading_tab.metaguiding_options
        page_count = self.intellireading_tab.page_count_options
        p["intellireading_enable_metaguiding"] = metaguiding.enable_metaguiding
        p["intellireading_include_about_page"] = metaguiding.include_about_page
        p["intellireading_fixation"] = metaguiding.fixation
        p["intellireading_bold_style"] = metaguiding.bold_style
        p["intellireading_bold_intensity"] = metaguiding.bold_intensity
        p["intellireading_enable_page_fix"] = page_count.enable_page_fix
        try:
            del p["intellireading_fix_existing_wordcounts"]
        except (KeyError, TypeError):
            pass
        return p
