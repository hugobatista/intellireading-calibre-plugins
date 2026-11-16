"""KEPUB parsing and clean word counting for the Kobo page-count fix."""

from __future__ import annotations

import posixpath
import re
import zipfile
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import unquote
from xml.etree import ElementTree as ET

from calibre_plugins.metaguidekobotouch import common, metaguiding

# The Kobo word counter counts each Han character as a word and uses word
# boundaries for the remaining scripts. This mirrors that behaviour on the
# host so the page count can be corrected without a clean copy on the device.
_HAN_RANGES = ((0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF), (0x20000, 0x2FA1F))
_BODY_RE = re.compile(r"<body[^>]*>(.*)</body>", re.DOTALL | re.IGNORECASE)
_BLOCK_TAG_RE = re.compile(
    r"</?(?:p|div|h[1-6]|li|ul|ol|tr|td|th|blockquote|pre|section|article|header|footer|aside|nav|title|br|hr)\b[^>]*>",
    re.IGNORECASE,
)
_TAG_RE = re.compile(r"<[^>]+>")
_WORD_RE = re.compile(r"\w+", re.UNICODE)

# Kobo's XHTML files are XML, but some navigation documents use HTML named
# entities that ElementTree cannot resolve on its own. Convert the common
# ones to numeric entities before parsing.
_NAMED_ENTITY_RE = re.compile(
    rb"&(nbsp|mdash|ndash|hellip|rsquo|lsquo|ldquo|rdquo|copy|reg|trade);"
)
_NAMED_ENTITY_VALUES = {
    b"nbsp": b"&#160;",
    b"mdash": b"&#8212;",
    b"ndash": b"&#8211;",
    b"hellip": b"&#8230;",
    b"rsquo": b"&#8217;",
    b"lsquo": b"&#8216;",
    b"ldquo": b"&#8220;",
    b"rdquo": b"&#8221;",
    b"copy": b"&#169;",
    b"reg": b"&#174;",
    b"trade": b"&#8482;",
}

# Approximate bytes-per-page unit used by the Kobo's file offset columns.
SIZE_DIVISOR = 12250.0


@dataclass
class TocEntry:
    path: str
    title: str
    depth: int


@dataclass
class KepubStructure:
    spine: List[str]
    toc: List[TocEntry]
    counts: List[int]
    sizes: List[float]
    offsets: List[int]


def is_han(character: str) -> bool:
    codepoint = ord(character)
    return any(start <= codepoint <= end for start, end in _HAN_RANGES)


def decode_xhtml(xhtml: bytes) -> str:
    try:
        encoding = metaguiding.RegExBoldMetaguider()._get_encoding(xhtml) or "utf-8"
    except Exception:
        encoding = "utf-8"
    try:
        return xhtml.decode(encoding, "replace")
    except LookupError:
        return xhtml.decode("utf-8", "replace")


def count_clean_words(xhtml: bytes) -> int:
    text = decode_xhtml(xhtml)
    match = _BODY_RE.search(text)
    body = match.group(1) if match else text
    body = _BLOCK_TAG_RE.sub(" ", body)
    body = _TAG_RE.sub("", body)
    han_count = sum(1 for character in body if is_han(character))
    rest = "".join(" " if is_han(character) else character for character in body)
    return han_count + len(_WORD_RE.findall(rest))


def _local_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _xml_bytes(data: bytes) -> bytes:
    def replace(match: re.Match[bytes]) -> bytes:
        return _NAMED_ENTITY_VALUES.get(match.group(1), match.group(0))

    return _NAMED_ENTITY_RE.sub(replace, data)


def _zip_member(zip_file: zipfile.ZipFile, path: str) -> Optional[str]:
    for candidate in (path, unquote(path)):
        try:
            return zip_file.getinfo(candidate).filename
        except KeyError:
            continue
    return None


def parse_spine(zip_file: zipfile.ZipFile) -> List[str]:
    names = zip_file.namelist()
    opf = next((name for name in names if name.lower().endswith(".opf")), None)
    if not opf:
        return []
    try:
        root = ET.fromstring(_xml_bytes(zip_file.read(opf)))
    except Exception as e:  # pylint: disable=broad-except
        common.log.debug(f"Could not parse KEPUB package document '{opf}': {e}")
        return []
    manifest_element = next(
        (element for element in root.iter() if _local_tag(element.tag) == "manifest"),
        None,
    )
    spine_element = next(
        (element for element in root.iter() if _local_tag(element.tag) == "spine"),
        None,
    )
    if manifest_element is None or spine_element is None:
        return []
    manifest: dict[str, str] = {}
    for item in list(manifest_element):
        item_id = item.get("id")
        href = item.get("href")
        if item_id and href:
            manifest[item_id] = href
    opf_dir = posixpath.dirname(opf)
    spine: List[str] = []
    for itemref in list(spine_element):
        if _local_tag(itemref.tag) != "itemref":
            continue
        href = manifest.get(itemref.get("idref") or "")
        if not href:
            continue
        path = (
            posixpath.normpath(posixpath.join(opf_dir, href))
            if opf_dir
            else posixpath.normpath(href)
        )
        path = path.split("#", 1)[0]
        if path:
            spine.append(path)
    return spine


def _resolve(base_dir: str, href: str) -> str:
    path = href.split("#", 1)[0]
    return posixpath.normpath(posixpath.join(base_dir, path)) if base_dir else posixpath.normpath(path)


def _toc_entries_from_nav(root: ET.Element, base_dir: str) -> List[TocEntry]:
    toc_nav = None
    fallback_nav = None
    for element in root.iter():
        if _local_tag(element.tag) != "nav":
            continue
        nav_type = element.get("{http://www.idpf.org/2007/ops}type")
        if nav_type == "toc":
            toc_nav = element
            break
        if nav_type in (None, "") and fallback_nav is None:
            fallback_nav = element
    nav = toc_nav or fallback_nav
    if nav is None:
        return []
    entries: List[TocEntry] = []

    def walk(element: ET.Element, depth: int) -> None:
        for child in list(element):
            tag = _local_tag(child.tag)
            if tag == "li":
                anchor = next(
                    (item for item in child if _local_tag(item.tag) == "a"),
                    None,
                )
                if anchor is not None and anchor.get("href"):
                    path = _resolve(base_dir, anchor.get("href", ""))
                    title = "".join(anchor.itertext()).strip()
                    entries.append(TocEntry(path, title, depth))
                for child_list in list(child):
                    if _local_tag(child_list.tag) in ("ol", "ul"):
                        walk(child_list, depth + 1)
            elif tag in ("ol", "ul"):
                walk(child, depth)

    walk(nav, 1)
    return entries


def _toc_entries_from_ncx(root: ET.Element, base_dir: str) -> List[TocEntry]:
    nav_map = next(
        (element for element in root.iter() if _local_tag(element.tag) == "navMap"),
        None,
    )
    if nav_map is None:
        return []
    entries: List[TocEntry] = []

    def walk(element: ET.Element, depth: int) -> None:
        for point in list(element):
            if _local_tag(point.tag) != "navPoint":
                continue
            content = next(
                (item for item in list(point) if _local_tag(item.tag) == "content"),
                None,
            )
            label = next(
                (item for item in point.iter() if _local_tag(item.tag) == "text"),
                None,
            )
            src = content.get("src") if content is not None else None
            if src:
                path = _resolve(base_dir, src)
                title = "".join(label.itertext()).strip() if label is not None else path
                entries.append(TocEntry(path, title, depth))
            walk(point, depth + 1)

    walk(nav_map, 1)
    return entries


def parse_toc(zip_file: zipfile.ZipFile) -> List[TocEntry]:
    names = zip_file.namelist()
    candidates = [name for name in names if name.lower().endswith("nav.xhtml")]
    candidates += [name for name in names if name.lower().endswith("toc.xhtml")]
    for nav_path in candidates:
        try:
            root = ET.fromstring(_xml_bytes(zip_file.read(nav_path)))
        except Exception as e:  # pylint: disable=broad-except
            common.log.debug(f"Could not parse KEPUB navigation document '{nav_path}': {e}")
            continue
        entries = _toc_entries_from_nav(root, posixpath.dirname(nav_path))
        if entries:
            return entries
    ncx_path = next((name for name in names if name.lower().endswith(".ncx")), None)
    if ncx_path:
        try:
            root = ET.fromstring(_xml_bytes(zip_file.read(ncx_path)))
        except Exception as e:  # pylint: disable=broad-except
            common.log.debug(f"Could not parse KEPUB NCX document '{ncx_path}': {e}")
            return []
        entries = _toc_entries_from_ncx(root, posixpath.dirname(ncx_path))
        if entries:
            return entries
    return []


def read_structure(device_path: str) -> Optional[KepubStructure]:
    """Read the spine, TOC and clean word counts from a KEPUB file."""
    try:
        with zipfile.ZipFile(device_path) as zip_file:
            spine = parse_spine(zip_file)
            if not spine:
                return None
            toc = parse_toc(zip_file)
            if not toc:
                return None
            counts: List[int] = []
            sizes: List[float] = []
            offsets: List[int] = []
            cumulative = 0.0
            for path in spine:
                member = _zip_member(zip_file, path)
                if member is None:
                    common.log.debug(
                        f"Spine item '{path}' not found in '{device_path}'; "
                        "skipping page-count fix"
                    )
                    return None
                counts.append(count_clean_words(zip_file.read(member)))
                size = zip_file.getinfo(member).file_size / SIZE_DIVISOR
                offsets.append(int(round(cumulative)))
                sizes.append(size)
                cumulative += size
            return KepubStructure(spine, toc, counts, sizes, offsets)
    except Exception as e:  # pylint: disable=broad-except
        common.log.debug(f"Could not read KEPUB structure from '{device_path}': {e}")
        return None
