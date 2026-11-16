"""User-facing messages for the Kobo Metaguide driver."""

MSG_ALREADY_METAGUIDED = (
    '"{name}" is already metaguided. '
    "Sending pre-metaguided EPUBs to a Kobo device may cause slow performance "
    "due to the kepubify process and the way it handles the bold tag.\n\n"
    "Recommended Process:\n"
    "1. Send the original non-metaguided EPUB to your Kobo\n"
    "2. Let this driver handle the metaguiding during transfer\n\n"
    "When the experimental page-count fix is enabled, the driver pre-creates "
    "the Kobo page counts during the transfer. No reconnect is needed for new "
    "books. Existing books and plain EPUB uploads are not modified.\n\n"
    "This ensures optimal performance on your device."
)

MSG_WELCOME = (
    "WARNING! PLEASE READ CAREFULLY: "
    "You have installed the 'KoboTouch Metaguide Driver' by IntelliReading.\n\n"
    "If you do not know what metaguiding is, DO NOT USE this driver "
    "and uninstall it immediately, as it is NOT required to send ebooks to your Kobo device. \n"
    "This driver will modify ANY epub/kepub file you send to the device, "
    "by adding additional markup to the text, like bold tags, eventually improving your reading experience, "
    "your focus and reading speed. \n\n"
    "🌐 For more information, visit https://go.hugobatista.com/gh/intellireading-calibre-plugins or "
    "https://go.hugobatista.com/intellireading .\n\n"
    "💙 Thank you for using IntelliReading!\n"
    "If this plugin improves your reading experience, please consider supporting "
    "its development through a donation: https://go.hugobatista.com/donate-intellireading ."
)
