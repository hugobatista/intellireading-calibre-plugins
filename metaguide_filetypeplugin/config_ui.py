"""
Configuration interface for the Epub Metaguider post processor plugin.
"""

__license__ = "GPL v3"
__copyright__ = "2025, Hugo Batista <intellireading at hugobatista.com>"
__docformat__ = "markdown en"

# pylint: disable=import-error
try:
    from qt.core import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QGroupBox, QLabel, QComboBox
except ImportError:
    from PyQt5.Qt import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QGroupBox, QLabel, QComboBox

from calibre_plugins.metaguidefiletype.config import prefs
from calibre_plugins.metaguidefiletype.metaguiding import (
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
    "Kobo kepubs and other WebKit-based readers."
)


class ConfigWidget(QWidget):
    """Configuration widget for the Epub Metaguider post processor plugin."""

    def __init__(self, plugin_action):
        """Initialize the configuration widget."""
        QWidget.__init__(self)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Event settings
        event_group = QGroupBox("When to Run")
        event_layout = QVBoxLayout()

        # Post-process checkbox
        self.postprocess_checkbox = QCheckBox("Enable metaguiding after conversion (post-process)", self)
        self.postprocess_checkbox.setChecked(prefs["enable_on_postprocess"])
        event_layout.addWidget(self.postprocess_checkbox)

        # Import checkbox
        self.import_checkbox = QCheckBox("Enable metaguiding when importing files", self)
        self.import_checkbox.setChecked(prefs["enable_on_import"])
        event_layout.addWidget(self.import_checkbox)

        event_group.setLayout(event_layout)
        self.layout.addWidget(event_group)

        # File type settings
        file_group = QGroupBox("File Types to Process")
        file_layout = QVBoxLayout()

        # EPUB checkbox
        self.epub_checkbox = QCheckBox("Process EPUB files", self)
        self.epub_checkbox.setChecked(prefs["process_epub"])
        file_layout.addWidget(self.epub_checkbox)

        # KEPUB checkbox
        self.kepub_checkbox = QCheckBox("Process KEPUB files", self)
        self.kepub_checkbox.setChecked(prefs["process_kepub"])
        file_layout.addWidget(self.kepub_checkbox)

        file_group.setLayout(file_layout)
        self.layout.addWidget(file_group)

        # EPUB content settings
        content_group = QGroupBox("EPUB Content")
        content_layout = QVBoxLayout()

        self.about_page_checkbox = QCheckBox("Add IntelliReading about/donation page", self)
        self.about_page_checkbox.setToolTip(
            "Adds an IntelliReading about/donation page at the end of metaguided EPUBs. "
            "Disable this to keep the EPUB content unchanged."
        )
        self.about_page_checkbox.setChecked(prefs["include_about_page"])
        content_layout.addWidget(self.about_page_checkbox)

        fixation_layout = QHBoxLayout()
        fixation_layout.addWidget(QLabel("Fixation level:", self))
        self.fixation_combo = QComboBox(self)
        for level in FIXATION_LEVELS:
            self.fixation_combo.addItem(str(level), level)
        fixation_index = self.fixation_combo.findData(prefs["fixation"])
        if fixation_index < 0:
            fixation_index = self.fixation_combo.findData(DEFAULT_FIXATION)
        self.fixation_combo.setCurrentIndex(fixation_index)
        self.fixation_combo.setToolTip("How much of each word is bolded. 1 = least bold, 5 = most bold. Default: 3.")
        fixation_layout.addWidget(self.fixation_combo)
        fixation_layout.addStretch()
        content_layout.addLayout(fixation_layout)

        bold_style_layout = QHBoxLayout()
        bold_style_layout.addWidget(QLabel("Bold style:", self))
        self.bold_style_combo = QComboBox(self)
        for style in BOLD_STYLES:
            self.bold_style_combo.addItem(_BOLD_STYLE_LABELS[style], style)
        bold_style_index = self.bold_style_combo.findData(prefs["bold_style"])
        if bold_style_index < 0:
            bold_style_index = self.bold_style_combo.findData(DEFAULT_BOLD_STYLE)
        self.bold_style_combo.setCurrentIndex(bold_style_index)
        self.bold_style_combo.setToolTip(_BOLD_STYLE_TOOLTIP)
        bold_style_layout.addWidget(self.bold_style_combo)
        bold_style_layout.addStretch()
        content_layout.addLayout(bold_style_layout)

        intensity_layout = QHBoxLayout()
        intensity_layout.addWidget(QLabel("Bold intensity:", self))
        self.bold_intensity_combo = QComboBox(self)
        for level in BOLD_INTENSITIES:
            self.bold_intensity_combo.addItem(str(level), level)
        intensity_index = self.bold_intensity_combo.findData(prefs["bold_intensity"])
        if intensity_index < 0:
            intensity_index = self.bold_intensity_combo.findData(DEFAULT_BOLD_INTENSITY)
        self.bold_intensity_combo.setCurrentIndex(intensity_index)
        self.bold_intensity_combo.setToolTip(
            "How strong the visual bold effect is: 1 = subtle, 5 = strongest. "
            "Only applies to Visual bold styles."
        )
        intensity_layout.addWidget(self.bold_intensity_combo)
        intensity_layout.addStretch()
        content_layout.addLayout(intensity_layout)

        self.bold_style_combo.currentIndexChanged.connect(self._update_bold_intensity_enabled)
        self._update_bold_intensity_enabled()

        content_group.setLayout(content_layout)
        self.layout.addWidget(content_group)

        # Add info label
        info_label = QLabel("Note: Changes will take effect after restarting Calibre")
        self.layout.addWidget(info_label)

        self.layout.addStretch()

    def _update_bold_intensity_enabled(self, *_args: object) -> None:
        self.bold_intensity_combo.setEnabled(self.bold_style_combo.currentData() != "tag")

    def save_settings(self):
        """Save the current configuration."""
        # Save event settings
        prefs["enable_on_postprocess"] = self.postprocess_checkbox.isChecked()
        prefs["enable_on_import"] = self.import_checkbox.isChecked()

        # Save file type settings
        prefs["process_epub"] = self.epub_checkbox.isChecked()
        prefs["process_kepub"] = self.kepub_checkbox.isChecked()

        # Save content settings
        prefs["include_about_page"] = self.about_page_checkbox.isChecked()

        # Save metaguiding settings
        prefs["fixation"] = int(self.fixation_combo.currentData())
        prefs["bold_style"] = self.bold_style_combo.currentData()
        prefs["bold_intensity"] = int(self.bold_intensity_combo.currentData())
