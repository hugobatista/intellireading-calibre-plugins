import logging
from io import BytesIO
import os
import posixpath
import sys
import traceback
import zipfile
from collections.abc import Generator
from html import escape
from typing import Any, cast
from urllib.parse import unquote
import math
import regex as re

# relative import is used to ensure that when this module gets copied to another location
# it still works
from .__about_cli__ import __version__ as cli_version  # noqa: TID252

_logger = logging.getLogger(__name__)
_METAGUIDED_FLAG_FILENAME = "intellireading.metaguide"
_ABOUT_PAGE_FILENAME = "intellireading-about.xhtml"
_ABOUT_PAGE_MANIFEST_ID = "intellireading-about"
_ABOUT_PAGE_GENERATOR = "IntelliReading Metaguiding"
_DONATION_URL = "https://go.hugobatista.com/donate-intellireading"
_WEBSITE_URL = "https://intellireading.com/"
_XML_BASE_ATTRIBUTE = "{http://www.w3.org/XML/1998/namespace}base"
_EPUB_EXTENSIONS = [".EPUB", ".KEPUB"]
_XHTML_EXTENSIONS = [".XHTML", ".HTML", ".HTM"]
_TOC_FILENAMES = ["nav.xhtml", "nav.html", "toc.xhtml", "toc.html"]

DEFAULT_FIXATION = 3
# Fraction of each word's characters that are bolded for each fixation level.
_FIXATION_RATIOS = {1: 0.30, 2: 0.40, 3: 0.50, 4: 0.60, 5: 0.70}
FIXATION_LEVELS = tuple(sorted(_FIXATION_RATIOS))
_THREE_LETTER_WORD_LENGTH = 3


def _validate_fixation(fixation: int) -> None:
    if isinstance(fixation, bool) or not isinstance(fixation, int) or fixation not in _FIXATION_RATIOS:
        msg = f"Invalid fixation level '{fixation}'. Valid levels are {FIXATION_LEVELS}"
        raise ValueError(msg)


def _generate_flag_file_content() -> bytes:
    """Generate the content for the metaguiding flag file.
    This includes version, process name, and call graph information.

    Returns:
        bytes: The encoded content of the flag file.
    """
    try:
        # Get process name - fallback to 'unknown' if sys.argv is not available
        try:
            process_name = os.path.basename(sys.argv[0])
        except (AttributeError, IndexError):
            process_name = "unknown"
            _logger.warning("Could not determine process name, using 'unknown'")

        # Get call stack information - handle potential traceback errors
        try:
            call_frames = traceback.extract_stack()
            # Skip the last frame (current function) and metaguide_epub_stream frame
            relevant_frames = call_frames[:-2]
            call_graph_path = " -> ".join(
                f"{os.path.basename(frame.filename)}:{frame.name}" for frame in relevant_frames
            )
        except Exception as e:
            call_graph_path = "unknown"
            _logger.warning(f"Could not generate call graph: {e}")

        # Build and return the flag content
        flag_lines = [f"version: {cli_version}", f"process: {process_name}", f"call_graph: {call_graph_path}"]
        return "\n".join(flag_lines).encode()
    except Exception as e:
        # If anything goes wrong, return a minimal flag file rather than failing
        _logger.error(f"Error generating flag file content: {e}")
        return f"version: {cli_version}\nprocess: unknown\ncall_graph: error".encode()


class RegExBoldMetaguider:
    _body_regex = re.compile(r"<body[^>]*>(.*)</body>", re.DOTALL)
    _text_block_regex = re.compile(r"(?<!<b[^>]*)>[^\S]*[^\s<][^<]*[^\S\n]*<")
    _bolded_text_block_regex = re.compile(r"<b>\b\w{1}\b</b>|<b>\b\w+\b</b>(?:\b\w+\b)")
    _word_pattern_regex = re.compile(r"\b\w+\b", re.UNICODE)
    _entity_ref_regex = re.compile(r"(&[#a-zA-Z][a-zA-Z0-9]*;)")
    _bolded_word_regex = re.compile(r"<b>(.*?)</b>")

    def __init__(self, fallback_encoding: str = "utf-8", *, fixation: int = DEFAULT_FIXATION) -> None:
        _validate_fixation(fixation)
        self._fallback_encoding = fallback_encoding
        self._fixation = fixation
        self._bold_ratio = _FIXATION_RATIOS[fixation]

    def _bold_word(self, word: str) -> str:
        # this is the function that is called for each word

        # if the word is an empty string, whitespace or new line, return it
        if not word.strip():
            return word

        word_length = len(word)
        bold_length = max(1, math.ceil(word_length * self._bold_ratio))
        if word_length == _THREE_LETTER_WORD_LENGTH and self._fixation <= DEFAULT_FIXATION:
            # keep the historical behaviour for three letter words up to the default level
            bold_length = 1
        if word_length > 1:
            # always leave at least one character unbolded
            bold_length = min(bold_length, word_length - 1)
        return f"<b>{word[:bold_length]}</b>{word[bold_length:]}"  # Bold the first part of the word

    def _unbold_word(self, word: str) -> str:
        # if the word is an empty string, whitespace or new line, return it
        if not word.strip():
            return word

        # short-circuit if the word is not bolded
        if "<b>" not in word:
            return word

        # remove the <b></b> tags
        return self._bolded_word_regex.sub(r"\1", word)

    def _bold_node_text_part(self, part: str) -> str:
        # is this part an entity reference?
        if self._entity_ref_regex.match(part):
            return part
        return self._word_pattern_regex.sub(lambda m: self._bold_word(m.group()), part)

    def _unbold_node_text_part(self, part: str) -> str:
        # skip if it's an entity reference
        if self._entity_ref_regex.match(part):
            _logger.debug(f"Skipping entity reference: {part}")
            return part
        # remove bold tags on all words found
        result = self._unbold_word(part)
        return result

    def _bold_text_node(self, node: str) -> str:
        # this is the function that is called for each text node
        node_text = node[1:-1]
        _logger.debug(f"Bold text node: {node_text}")

        # split the node_text into parts based on the entity references
        node_text_parts = self._entity_ref_regex.split(node_text)

        new_node_text = "".join(map(self._bold_node_text_part, node_text_parts))

        if node_text != new_node_text:
            return ">" + new_node_text + "<"
        return node

    def _bold_document(self, html: str, *, remove_metaguiding: bool = False) -> str:
        # get the body. If there is no body, return the original html
        match = self._body_regex.search(html)
        if not match:
            return html

        body = match.group(1)
        if not remove_metaguiding:
            # find all text nodes in the body and trigger the bolding of the words
            body = self._text_block_regex.sub(
                lambda m: self._bold_text_node(m.group()),
                body,
            )
        else:
            body = self._bolded_text_block_regex.sub(lambda m: self._unbold_node_text_part(m.group()), body)

        _logger.debug(f"Bolded body: {body}")

        html = html.replace(match.group(1), body)
        return html

    def _get_encoding_using_lxml(self, xhtml_document: bytes) -> str | None:
        from lxml import etree

        try:
            parser = etree.XMLParser(resolve_entities=False)
            doc = etree.fromstring(xhtml_document, parser=parser).getroottree()
            docinfo = doc.docinfo
            return cast(str | None, docinfo.encoding)
        except etree.XMLSyntaxError:
            return None

    def _get_encoding_using_bom(self, xhtml_document: bytes) -> str | None:
        if xhtml_document.startswith(b"\xef\xbb\xbf"):
            return "utf-8"
        elif xhtml_document.startswith(b"\xff\xfe"):
            return "utf-16-le"
        elif xhtml_document.startswith(b"\xfe\xff"):
            return "utf-16-be"
        elif xhtml_document.startswith(b"\x00\x00\xfe\xff"):
            return "utf-32-be"
        elif xhtml_document.startswith(b"\xff\xfe\x00\x00"):
            return "utf-32-le"
        else:
            return None

    def _get_encoding_using_xml_header(self, xhtml_document: bytes) -> str | None:
        # if the document does not start with an XML header, return None. This is not a xml document
        if not xhtml_document.startswith(b"<?xml "):
            return None

        xml_header_end = xhtml_document.find(b"?>")
        if xml_header_end == -1:
            # a truncated XML header is invalid, but should not prevent the remaining
            # encoding detectors (BOM and lxml) from running
            _logger.debug("XML header has no closing '?>'. Trying other encoding detection methods.")
            return None

        header = xhtml_document[: xml_header_end + 2].decode("utf-8")
        match = re.search(r'encoding=(["\'])([a-zA-Z][a-zA-Z0-9-]{0,38}[a-zA-Z0-9])\1', header)
        if match:
            return cast(str, match.group(2))
        else:
            # although the XML header is present, it does not contain an encoding
            # this is not a valid XHTML document, but we can still try to detect the encoding on a later stage
            # and we will not raise an exception
            return None

    def _get_encoding(self, xhtml_document: bytes) -> str:
        encoding = self._get_encoding_using_xml_header(xhtml_document)

        if not encoding:
            _logger.debug(
                "Could not detect the encoding of the XHTML document using the XML header. "
                "Trying to detect the encoding using the BOM."
            )
            encoding = self._get_encoding_using_bom(xhtml_document)

        if not encoding:
            _logger.debug(
                "Could not detect the encoding of the XHTML document. Trying to detect the encoding using lxml."
            )
            encoding = self._get_encoding_using_lxml(xhtml_document)

        return encoding or self._fallback_encoding

    def metaguide_xhtml_document(self, xhtml_document: bytes, *, remove_metaguiding: bool = False) -> bytes:
        # if none of the methods to detect the encoding work, use utf-8
        encoding = self._get_encoding(xhtml_document) or "utf-8"

        html = xhtml_document.decode(encoding)
        bolded_html = self._bold_document(html, remove_metaguiding=remove_metaguiding)
        return bolded_html.encode(encoding)


class _EpubItemFile:
    def __init__(self, filename: str | None = None, content: bytes = b"") -> None:
        self.filename = filename
        self.content = content
        _extension = (self.filename and os.path.splitext(self.filename)[-1].upper()) or None

        # some epub have files with html extension but they are xml files
        self.is_xhtml_document = _extension in _XHTML_EXTENSIONS
        # check whether the file is a table of contents or navigation file
        # by checking the filename against a list of known TOC filenames
        # this is a heuristic and may not be 100% accurate.
        # Separate the directory check from the filename check
        self.is_toc_document = False
        self.is_about_page = False
        if self.filename:
            # Normalize the filename to lowercase for comparison and remove the directory part
            filename_base = os.path.basename(self.filename.lower())
            self.is_toc_document = filename_base in _TOC_FILENAMES
            self.is_about_page = filename_base == _ABOUT_PAGE_FILENAME
        self.metaguided = False  # flag to indicate if the file has been metaguided. Useful for multi-threading

    def __str__(self) -> str:
        return f"{self.filename} ({len(self.content)} bytes)"

    def metaguide(self, metaguider: RegExBoldMetaguider, *, remove_metaguiding: bool = False) -> None:
        if not remove_metaguiding and self.metaguided:
            _logger.warning(f"File {self.filename} already metaguided, skipping")
        elif self.is_toc_document or self.is_about_page:
            _logger.debug(f"Skipping nav/toc/about page file {self.filename}")
        elif self.is_xhtml_document:
            _logger.debug(f"Metaguiding file {self.filename}")
            self.content = metaguider.metaguide_xhtml_document(self.content, remove_metaguiding=remove_metaguiding)
            self.metaguided = True
            _logger.debug(f"Metaguided file {self.filename}")
        else:
            _logger.debug(f"Skipping file {self.filename}")


def _get_local_name(element: Any) -> str | None:
    tag = getattr(element, "tag", None)
    if not isinstance(tag, str):
        return None
    return tag.rsplit("}", 1)[-1]


def _find_child_by_local_name(parent: Any, local_name: str) -> Any | None:
    for child in parent:
        if _get_local_name(child) == local_name:
            return child
    return None


def _qualified_tag(parent: Any, local_name: str) -> str:
    tag = getattr(parent, "tag", None)
    if isinstance(tag, str) and tag.startswith("{"):
        namespace = tag[1:].split("}", 1)[0]
        return f"{{{namespace}}}{local_name}"
    return local_name


def _find_opf_path(epub_item_files: list[_EpubItemFile]) -> str | None:
    container_item = next((f for f in epub_item_files if f.filename == "META-INF/container.xml"), None)
    if container_item is not None:
        try:
            from lxml import etree

            parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
            container_root = etree.fromstring(container_item.content, parser)
            for element in container_root.iter():
                if _get_local_name(element) != "rootfile":
                    continue
                full_path = (element.get("full-path") or "").strip()
                media_type = (element.get("media-type") or "").strip()
                if not full_path or (media_type and media_type != "application/oebps-package+xml"):
                    continue
                candidates = [full_path, posixpath.normpath(full_path)]
                unquoted_path = unquote(full_path)
                if unquoted_path != full_path:
                    candidates.extend([unquoted_path, posixpath.normpath(unquoted_path)])
                for candidate in candidates:
                    if any(f.filename == candidate for f in epub_item_files):
                        return candidate
                _logger.warning(f"OPF path '{full_path}' from container.xml was not found in the EPUB")
        except Exception as e:
            _logger.warning(f"Could not read META-INF/container.xml: {e}")

    opf_filenames = [f.filename for f in epub_item_files if f.filename and f.filename.lower().endswith(".opf")]
    if len(opf_filenames) == 1:
        return opf_filenames[0]

    _logger.warning("Could not determine the EPUB package document (OPF) path")
    return None


def _find_item_by_filename(epub_item_files: list[_EpubItemFile], filename: str) -> _EpubItemFile | None:
    return next((f for f in epub_item_files if f.filename == filename), None)


def _build_about_page(epub_version: str, tool_version: str = cli_version) -> bytes:
    """Build the about/donation page.

    Visible URLs are wrapped in <b> so the metaguider does not split them into bold fragments.
    """
    version = escape(tool_version)
    if epub_version.strip().startswith(("1", "2")):
        doctype = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">'
        charset_meta = '<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>'
    else:
        doctype = "<!DOCTYPE html>"
        charset_meta = '<meta charset="utf-8"/>'

    return f"""<?xml version="1.0" encoding="utf-8"?>
{doctype}
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" dir="ltr">
<head>
  {charset_meta}
  <meta name="generator" content="{_ABOUT_PAGE_GENERATOR} {version}"/>
  <title>Thank you for using IntelliReading</title>
</head>
<body>
  <h1>Thank you for using IntelliReading</h1>
  <p>This ebook was metaguided with <strong>IntelliReading Metaguiding</strong> (version {version}).</p>
  <p>IntelliReading is free and open source. If it improves your reading experience, please consider supporting
  its development with a donation. Your contribution helps keep these tools free and improving for the reading
  community.</p>
  <p><strong>Donate:</strong><br/>
  <a href="{_DONATION_URL}"><b>{_DONATION_URL}</b></a></p>
  <p><strong>Learn more:</strong><br/>
  <a href="{_WEBSITE_URL}"><b>{_WEBSITE_URL}</b></a></p>
  <hr/>
  <p><small>This page was added automatically by IntelliReading Metaguiding.
  You can turn off the about page in the options of the tool used to convert this EPUB.
  Removing metaguiding also removes this page.</small></p>
</body>
</html>
""".encode()


def _is_fixed_layout(opf_root: Any) -> bool:
    for element in opf_root.iter():
        local_name = _get_local_name(element)
        if local_name == "meta":
            property_name = (element.get("property") or "").strip()
            property_value = (element.text or "").strip()
            if property_name == "rendition:layout" and property_value == "pre-paginated":
                return True
            if element.get("name") == "fixed-layout" and (element.get("content") or "").strip().lower() == "true":
                return True
        elif local_name == "itemref":
            properties = (element.get("properties") or "").split()
            if "rendition:layout-pre-paginated" in properties:
                return True
    return False


def _is_apple_fixed_layout(epub_item_files: list[_EpubItemFile]) -> bool:
    options_item = next(
        (f for f in epub_item_files if f.filename == "META-INF/com.apple.ibooks.display-options.xml"),
        None,
    )
    if options_item is None:
        return False

    try:
        from lxml import etree

        parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
        options_root = etree.fromstring(options_item.content, parser)
    except Exception as e:
        _logger.debug(f"Could not parse Apple iBooks display options: {e}")
        return False

    for option in options_root.iter():
        if _get_local_name(option) != "option":
            continue
        if option.get("name") == "fixed-layout" and (option.text or "").strip().lower() == "true":
            return True
    return False


def _href_basename(href: str) -> str:
    href_path = unquote(href.split("#", 1)[0].split("?", 1)[0])
    return posixpath.basename(href_path).lower()


def _has_about_page_file(epub_item_files: list[_EpubItemFile]) -> bool:
    about_page_filename = _ABOUT_PAGE_FILENAME.lower()
    return any(
        epub_item_file.filename and posixpath.basename(epub_item_file.filename).lower() == about_page_filename
        for epub_item_file in epub_item_files
    )


def _manifest_has_about_page(manifest: Any) -> bool:
    about_page_id = _ABOUT_PAGE_MANIFEST_ID.lower()
    about_page_filename = _ABOUT_PAGE_FILENAME.lower()
    for item in manifest:
        if _get_local_name(item) != "item":
            continue
        if (item.get("id") or "").lower() == about_page_id:
            return True
        href = item.get("href")
        if href and _href_basename(href) == about_page_filename:
            return True
    return False


def _spine_has_about_page(spine: Any) -> bool:
    about_page_id = _ABOUT_PAGE_MANIFEST_ID.lower()
    for itemref in spine:
        if _get_local_name(itemref) != "itemref":
            continue
        if (itemref.get("idref") or "").lower() == about_page_id:
            return True
    return False


def _opf_has_about_page(manifest: Any, spine: Any) -> bool:
    return _manifest_has_about_page(manifest) or _spine_has_about_page(spine)


def _resolve_href_paths(opf_dir: str, href: str) -> set[str]:
    href_path = href.split("#", 1)[0].split("?", 1)[0].strip()
    if not href_path:
        return set()
    if href_path.startswith("/"):
        href_path = href_path.lstrip("/")
    normalized = posixpath.normpath(posixpath.join(opf_dir, href_path) if opf_dir else href_path)
    return {normalized, unquote(normalized)}


def _serialize_opf_document(tree: Any) -> bytes:
    from lxml import etree

    tostring_kwargs: dict[str, Any] = {}
    if tree.docinfo.doctype:
        tostring_kwargs["doctype"] = tree.docinfo.doctype
    if tree.docinfo.standalone is not None:
        tostring_kwargs["standalone"] = tree.docinfo.standalone
    return cast(
        bytes,
        etree.tostring(
            tree,
            xml_declaration=True,
            encoding=tree.docinfo.encoding or "utf-8",
            **tostring_kwargs,
        ),
    )


def _inject_about_page(epub_item_files: list[_EpubItemFile], metaguider: RegExBoldMetaguider) -> bool:
    opf_path = _find_opf_path(epub_item_files)
    if not opf_path:
        return False

    opf_item = _find_item_by_filename(epub_item_files, opf_path)
    if opf_item is None:
        _logger.warning(f"OPF file '{opf_path}' was not found in the EPUB, skipping about page")
        return False

    opf_dir = posixpath.dirname(opf_path)
    page_path = posixpath.join(opf_dir, _ABOUT_PAGE_FILENAME) if opf_dir else _ABOUT_PAGE_FILENAME
    if _has_about_page_file(epub_item_files):
        _logger.debug("An IntelliReading about page file already exists, skipping")
        return False

    try:
        from lxml import etree
    except ImportError as e:
        _logger.warning(f"Could not import lxml, skipping about page: {e}")
        return False

    try:
        parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, remove_blank_text=False)
        tree = etree.fromstring(opf_item.content, parser).getroottree()
        opf_root = tree.getroot()
    except Exception as e:
        _logger.warning(f"Could not parse OPF file '{opf_path}', skipping about page: {e}")
        return False

    manifest = _find_child_by_local_name(opf_root, "manifest")
    spine = _find_child_by_local_name(opf_root, "spine")
    if manifest is None or spine is None:
        _logger.warning(f"OPF file '{opf_path}' has no manifest or spine, skipping about page")
        return False

    if opf_root.get(_XML_BASE_ATTRIBUTE) or manifest.get(_XML_BASE_ATTRIBUTE) or spine.get(_XML_BASE_ATTRIBUTE):
        _logger.warning(f"OPF file '{opf_path}' uses xml:base, skipping about page")
        return False

    if _is_fixed_layout(opf_root) or _is_apple_fixed_layout(epub_item_files):
        _logger.info(f"Skipping about page for fixed-layout EPUB '{opf_path}'")
        return False

    if _opf_has_about_page(manifest, spine):
        _logger.debug(f"About page is already listed in '{opf_path}', skipping")
        return False

    epub_version = (opf_root.get("version") or "3.0").strip()
    page_content = metaguider.metaguide_xhtml_document(_build_about_page(epub_version))

    item = etree.SubElement(manifest, _qualified_tag(manifest, "item"))
    item.set("id", _ABOUT_PAGE_MANIFEST_ID)
    item.set("href", _ABOUT_PAGE_FILENAME)
    item.set("media-type", "application/xhtml+xml")

    itemref = etree.SubElement(spine, _qualified_tag(spine, "itemref"))
    itemref.set("idref", _ABOUT_PAGE_MANIFEST_ID)

    try:
        opf_item.content = _serialize_opf_document(tree)
    except Exception as e:
        _logger.warning(f"Could not serialize OPF file '{opf_path}', skipping about page: {e}")
        return False

    epub_item_files.append(_EpubItemFile(page_path, page_content))
    _logger.info(f"Added IntelliReading about page to '{opf_path}'")
    return True


def _remove_about_page(epub_item_files: list[_EpubItemFile]) -> bool:
    opf_path = _find_opf_path(epub_item_files)
    if not opf_path:
        _logger.warning("Could not determine the OPF path, cannot remove the IntelliReading about page")
        return False

    opf_item = _find_item_by_filename(epub_item_files, opf_path)
    if opf_item is None:
        _logger.warning(f"OPF file '{opf_path}' was not found in the EPUB, cannot remove the about page")
        return False

    try:
        from lxml import etree

        parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, remove_blank_text=False)
        tree = etree.fromstring(opf_item.content, parser).getroottree()
        opf_root = tree.getroot()
    except Exception as e:
        _logger.warning(f"Could not parse OPF file '{opf_path}', cannot remove the about page: {e}")
        return False

    opf_dir = posixpath.dirname(opf_path)
    page_path = posixpath.join(opf_dir, _ABOUT_PAGE_FILENAME) if opf_dir else _ABOUT_PAGE_FILENAME
    removed_paths = {page_path}
    removed_ids: set[str] = set()
    removed_opf_entries = False

    manifest = _find_child_by_local_name(opf_root, "manifest")
    if manifest is not None:
        for item in list(manifest):
            if _get_local_name(item) != "item":
                continue
            item_id = (item.get("id") or "").lower()
            href = item.get("href") or ""
            href_basename = _href_basename(href) if href else ""
            if item_id == _ABOUT_PAGE_MANIFEST_ID.lower() or href_basename == _ABOUT_PAGE_FILENAME.lower():
                if item_id:
                    removed_ids.add(item_id)
                removed_paths.update(_resolve_href_paths(opf_dir, href))
                manifest.remove(item)
                removed_opf_entries = True

    spine = _find_child_by_local_name(opf_root, "spine")
    if spine is not None:
        for itemref in list(spine):
            if _get_local_name(itemref) != "itemref":
                continue
            idref = (itemref.get("idref") or "").lower()
            if idref in removed_ids or idref == _ABOUT_PAGE_MANIFEST_ID.lower():
                spine.remove(itemref)
                removed_opf_entries = True

    if removed_opf_entries:
        try:
            opf_item.content = _serialize_opf_document(tree)
        except Exception as e:
            _logger.warning(f"Could not serialize OPF file '{opf_path}', cannot remove the about page: {e}")
            return False

    original_file_count = len(epub_item_files)
    removed_paths_lower = {path.lower() for path in removed_paths}
    about_page_filename = _ABOUT_PAGE_FILENAME.lower()
    epub_item_files[:] = [
        epub_item_file
        for epub_item_file in epub_item_files
        if not (
            epub_item_file.filename
            and (
                epub_item_file.filename.lower() in removed_paths_lower
                or posixpath.basename(epub_item_file.filename).lower() == about_page_filename
            )
        )
    ]
    removed_page_file = len(epub_item_files) != original_file_count

    if removed_opf_entries or removed_page_file:
        _logger.info(f"Removed IntelliReading about page from '{opf_path}'")
        return True

    _logger.debug(f"No IntelliReading about page found in '{opf_path}'")
    return False


def _get_epub_item_files_from_zip(input_zip: zipfile.ZipFile) -> list[_EpubItemFile]:
    def read_compressed_file(input_zip: zipfile.ZipFile, filename: str) -> _EpubItemFile:
        return _EpubItemFile(filename, input_zip.read(filename))

    epub_item_files = [read_compressed_file(input_zip, f.filename) for f in input_zip.infolist()]
    _logger.debug(f"Read {len(epub_item_files)} files from input file")
    return epub_item_files


def _process_epub_item_files(
    epub_item_files: list[_EpubItemFile], *, metaguider: RegExBoldMetaguider, remove_metaguiding: bool = False
) -> Generator[_EpubItemFile]:
    for epub_item_file in epub_item_files:
        _logger.debug(f"Processing file '{epub_item_file.filename}' remove_metaguiding={remove_metaguiding}")
        epub_item_file.metaguide(metaguider, remove_metaguiding=remove_metaguiding)
        yield epub_item_file


def _write_item_files_to_zip(epub_item_files: list[_EpubItemFile], output_zip: zipfile.ZipFile) -> None:
    def write_compressed_file(output_zip: zipfile.ZipFile, epub_item_file: _EpubItemFile) -> None:
        if epub_item_file.filename is None:
            msg = "EpubItemFile.filename is None"
            raise ValueError(msg)

        _logger.debug(f"Writing file {epub_item_file.filename} to output zip {output_zip.filename}")
        with output_zip.open(epub_item_file.filename, mode="w") as compressed_output_file:
            compressed_output_file.write(epub_item_file.content)

    for _epub_item_file in epub_item_files:
        write_compressed_file(output_zip, _epub_item_file)


def _ensure_file_exists(input_file: str) -> None:
    if not os.path.isfile(input_file):
        exception_message = f"Input file '{input_file}' does not exist"
        _logger.error(exception_message)
        raise ValueError(exception_message)


def _ensure_allowed_extension(input_file: str, extensions: list[str]) -> None:
    file_extension = os.path.splitext(input_file)[-1].upper()
    if file_extension not in extensions:
        exception_message = f"Input file '{input_file}' extension is not in {extensions}"
        _logger.error(exception_message)
        raise ValueError(exception_message)


def _check_flag_file(
    epub_item_files: list[_EpubItemFile], *, remove_metaguiding: bool = False
) -> tuple[bool, _EpubItemFile | None]:
    """Check if an epub file is already metaguided by looking for the flag file.

    Args:
        epub_item_files: List of files in the epub
        remove_metaguiding: Whether we're removing metaguiding

    Returns:
        Tuple of (is_already_metaguided, flag_file)
    """
    flag_file = next((f for f in epub_item_files if f.filename == _METAGUIDED_FLAG_FILENAME), None)
    is_already_metaguided = not remove_metaguiding and flag_file is not None

    if is_already_metaguided:
        try:
            _logger.debug("Epub already metaguided, flag file content:")
            if flag_file:
                _logger.debug(flag_file.content.decode("utf-8"))
            else:
                _logger.debug("Flag file found but content could not be read")
        except Exception as e:
            _logger.debug(f"Could not decode flag file content: {e}")

    return is_already_metaguided, flag_file


def metaguide_epub_file(
    input_file: str,
    output_file: str,
    *,
    remove_metaguiding: bool = False,
    include_about_page: bool = True,
    fixation: int = DEFAULT_FIXATION,
) -> None:
    """Metaguide an epub file
    input_file: str
        The input epub file
    output_file: str
        The output epub file
    remove_metaguiding: bool
        If True, removes metaguiding from the epub file
    include_about_page: bool
        If True, adds the IntelliReading about/donation page to the end of the epub
    fixation: int
        How much of each word is bolded, from 1 (least) to 5 (most). Defaults to 3
    """

    _logger.debug(f"Processing file '{input_file}' to output '{output_file}'")
    _ensure_file_exists(input_file)
    _ensure_allowed_extension(input_file, _EPUB_EXTENSIONS)

    with open(input_file, "rb") as input_reader:
        input_file_stream = BytesIO(input_reader.read())
        output_file_stream = metaguide_epub_stream(
            input_file_stream,
            remove_metaguiding=remove_metaguiding,
            include_about_page=include_about_page,
            fixation=fixation,
        )
        with open(output_file, "wb") as output_writer:
            output_writer.write(output_file_stream.read())


def metaguide_epub_stream(
    input_stream: BytesIO,
    *,
    remove_metaguiding: bool = False,
    include_about_page: bool = True,
    fixation: int = DEFAULT_FIXATION,
) -> BytesIO:
    """Metaguide an epub input stream
    input_file_stream: BytesIO
        The input epub file stream
    remove_metaguiding: bool
        If True, removes metaguiding from the epub file
    include_about_page: bool
        If True, adds the IntelliReading about/donation page to the end of the epub
    fixation: int
        How much of each word is bolded, from 1 (least) to 5 (most). Defaults to 3
    return: BytesIO
        The metaguided epub file stream
    """
    output_stream = BytesIO()
    metaguider = RegExBoldMetaguider(fixation=fixation)

    if remove_metaguiding:
        _logger.debug("Removing metaguiding from epub")
    else:
        _logger.debug("Metaguiding epub")

    _logger.debug("Getting item files")
    with zipfile.ZipFile(input_stream, "r", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as input_zip:
        with zipfile.ZipFile(output_stream, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as output_zip:
            _logger.debug("Processing zip: Getting item files")
            epub_item_files = _get_epub_item_files_from_zip(input_zip)

            # Check if the file is already metaguided
            is_already_metaguided, _ = _check_flag_file(epub_item_files, remove_metaguiding=remove_metaguiding)

            if is_already_metaguided:
                _logger.debug("Copying files while preserving structure...")
                # Even for already metaguided files, we need to properly process through zip mechanisms
                for item in input_zip.filelist:
                    with input_zip.open(item.filename) as source, output_zip.open(item.filename, "w") as target:
                        _logger.debug(f"Copying file {item.filename} with original compression")
                        target.write(source.read())
            else:
                processed_item_files = list(
                    _process_epub_item_files(
                        epub_item_files, metaguider=metaguider, remove_metaguiding=remove_metaguiding
                    )
                )

                if remove_metaguiding:
                    # remove the about page and the metaguided flag file
                    _remove_about_page(processed_item_files)
                    filtered_files = filter(lambda f: f.filename != _METAGUIDED_FLAG_FILENAME, processed_item_files)
                    processed_item_files = list(filtered_files)
                else:
                    if include_about_page:
                        _inject_about_page(processed_item_files, metaguider)
                    _logger.debug("Processing zip: Adding metaguided flag file")
                    flag_content = _generate_flag_file_content()
                    processed_item_files.append(_EpubItemFile(_METAGUIDED_FLAG_FILENAME, flag_content))

                _logger.debug("Processing zip: Writing output zip")
                _write_item_files_to_zip(processed_item_files, output_zip)

    output_stream.seek(0)
    return output_stream


def metaguide_xhtml_file(
    input_file: str, output_file: str, *, remove_metaguiding: bool = False, fixation: int = DEFAULT_FIXATION
) -> None:
    """Metaguide an xhtml file
    input_file: str
        The input xhtml file
    output_file: str
        The output xhtml file
    remove_metaguiding: bool
        If True, removes metaguiding from the xhtml file
    fixation: int
        How much of each word is bolded, from 1 (least) to 5 (most). Defaults to 3
    """
    _logger.debug(f"Processing file '{input_file}' to output '{output_file}'")
    _ensure_file_exists(input_file)
    _ensure_allowed_extension(input_file, _XHTML_EXTENSIONS)

    with open(input_file, "rb") as input_reader:
        input_file_stream = BytesIO(input_reader.read())
        output_file_stream = metaguide_xhtml_stream(
            input_file_stream, remove_metaguiding=remove_metaguiding, fixation=fixation
        )
    output_file_stream.seek(0)
    with open(output_file, "wb") as output_writer:
        output_writer.write(output_file_stream.read())


def metaguide_xhtml_stream(
    input_file_stream: BytesIO, *, remove_metaguiding: bool = False, fixation: int = DEFAULT_FIXATION
) -> BytesIO:
    """Metaguide an xhtml input stream
    input_file_stream: BytesIO
        The input xhtml file stream
    remove_metaguiding: bool
        If True, removes metaguiding from the xhtml file
    fixation: int
        How much of each word is bolded, from 1 (least) to 5 (most). Defaults to 3
    return: BytesIO
        The metaguided xhtml file stream
    """
    metaguider = RegExBoldMetaguider(fixation=fixation)
    output_file_stream = BytesIO()
    output_file_stream.write(
        metaguider.metaguide_xhtml_document(input_file_stream.read(), remove_metaguiding=remove_metaguiding)
    )
    output_file_stream.seek(0)
    return output_file_stream


def metaguide_dir(
    input_dir: str,
    output_dir: str,
    *,
    remove_metaguiding: bool = False,
    include_about_page: bool = True,
    fixation: int = DEFAULT_FIXATION,
) -> None:
    """Metaguides all epubs and xhtml found in a directory (recursively)
    input_dir: str
        The input epub/xhtml directory
    output_dir: str
        The output epub/xhtml directory
    remove_metaguiding: bool
        If True, removes metaguiding from the files
    include_about_page: bool
        If True, adds the IntelliReading about/donation page to the end of epub files
    fixation: int
        How much of each word is bolded, from 1 (least) to 5 (most). Defaults to 3
    """

    _validate_fixation(fixation)

    # get a list of all the files in the directory, and the child directories if recursive
    # verify if the file is a file and if it has the correct extension
    def get_files(directory: str, *, recursive: bool) -> Generator[str]:
        for filename in os.listdir(directory):
            input_filename = os.path.join(directory, filename)

            extension = os.path.splitext(input_filename)[-1].upper()
            if os.path.isfile(input_filename) and (extension in _EPUB_EXTENSIONS or extension in _XHTML_EXTENSIONS):
                yield input_filename
            elif os.path.isdir(input_filename) and recursive:
                yield from get_files(input_filename, recursive=recursive)

    _logger.info(f"Processing files in {input_dir} to {output_dir} (recursively)")

    files_processed = 0
    files_skipped = 0
    files_with_errors = 0

    # check if the output directory exists and if not create it
    if not os.path.exists(output_dir):
        _logger.info(f"Creating {output_dir}")
        os.makedirs(output_dir)

    for input_filename in get_files(input_dir, recursive=True):
        output_filename = os.path.join(output_dir, os.path.basename(input_filename))
        _logger.debug(f"Processing {input_filename} to {output_filename}")

        # verify if the output file already exists
        if os.path.isfile(output_filename):
            _logger.warning(f"Skipping {input_filename} because {output_filename} already exists")
            files_skipped += 1
            continue

        try:
            with open(input_filename, "rb") as input_reader:
                input_file_stream = BytesIO(input_reader.read())
                if os.path.splitext(input_filename)[-1].upper() in _EPUB_EXTENSIONS:
                    output_file_stream = metaguide_epub_stream(
                        input_file_stream,
                        remove_metaguiding=remove_metaguiding,
                        include_about_page=include_about_page,
                        fixation=fixation,
                    )
                else:
                    output_file_stream = metaguide_xhtml_stream(
                        input_file_stream, remove_metaguiding=remove_metaguiding, fixation=fixation
                    )
                with open(output_filename, "wb") as output_writer:
                    output_writer.write(output_file_stream.read())
            files_processed += 1
        except Exception as e:  # pylint: disable=broad-except
            # pylint: disable=logging-fstring-interpolation
            files_with_errors += 1
            _logger.exception(f"Error processing {input_filename}", e)
            continue


def is_file_metaguided(filepath: str) -> bool:
    """Check if a file has already been metaguided.

    Args:
        filepath: Path to the epub file to check

    Returns:
        bool: True if the file has already been metaguided, False otherwise

    Raises:
        ValueError: If the file doesn't exist or has an invalid extension
    """
    _ensure_file_exists(filepath)
    _ensure_allowed_extension(filepath, _EPUB_EXTENSIONS)

    with open(filepath, "rb") as input_reader:
        input_file_stream = BytesIO(input_reader.read())
        with zipfile.ZipFile(input_file_stream, "r", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as input_zip:
            epub_item_files = _get_epub_item_files_from_zip(input_zip)
            is_metaguided, _ = _check_flag_file(epub_item_files)
            return is_metaguided
