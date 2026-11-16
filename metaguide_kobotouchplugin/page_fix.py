"""DB-first page count support for the Kobo Metaguide driver."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any, List, Optional
from urllib.parse import unquote

from calibre.ebooks.metadata.book.base import Metadata

from calibre_plugins.metaguidekobotouch import common
from calibre_plugins.metaguidekobotouch.kepub import KepubStructure, read_structure

KEPUB_MIME = "application/x-kobo-epub+zip"
XHTML_MIME = "application/xhtml+xml"

_TITLE_EXT_RE = re.compile(r"\.kepub(\.epub)?$", re.IGNORECASE)


def _book_path(content_id: str) -> str:
    return content_id[len("file://"):] if content_id.startswith("file://") else content_id


def _normalize_content_id(content_id: str) -> str:
    if content_id.startswith("file://"):
        return content_id.replace(
            "file:///mnt/onboard//", "file:///mnt/onboard/"
        ).replace("file:///mnt/sd//", "file:///mnt/sd/")
    if content_id.startswith("/mnt/onboard/") or content_id.startswith("/mnt/sd/"):
        return "file://" + content_id
    return content_id


def _image_id(content_id: str) -> str:
    return content_id.replace(":", "_").replace("/", "_").replace(".", "_")


def _book_title(device_name: str, mi: Optional[Metadata]) -> str:
    title = getattr(mi, "title", None)
    if title:
        return str(title)
    return _TITLE_EXT_RE.sub("", os.path.basename(device_name))


def _table_exists(connection: Any, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone() is not None


def _content_columns(connection: Any) -> set[str]:
    return {row[1] for row in connection.execute("PRAGMA table_info(content)")}


def _insert_content_row(connection: Any, columns: set[str], row: dict[str, Any]) -> None:
    row = {key: value for key, value in row.items() if key in columns}
    if not row:
        return
    quoted = ",".join(f'"{column}"' for column in row)
    placeholders = ",".join("?" for _ in row)
    connection.execute(
        f"INSERT OR REPLACE INTO content ({quoted}) VALUES ({placeholders})",
        list(row.values()),
    )


def _book_row(
    content_id: str,
    title: str,
    mi: Optional[Metadata],
    file_size: int,
    chapter_count: int,
    now_local: str,
    now_utc: str,
) -> dict[str, Any]:
    authors = getattr(mi, "authors", None) or []
    series_index = getattr(mi, "series_index", None)
    return {
        "ContentID": content_id,
        "ContentType": "6",
        "MimeType": KEPUB_MIME,
        "BookID": None,
        "BookTitle": title,
        "Title": title,
        "Attribution": " & ".join(str(author) for author in authors),
        "Description": getattr(mi, "comments", None),
        "Publisher": getattr(mi, "publisher", None),
        "ISBN": getattr(mi, "isbn", None),
        "Series": getattr(mi, "series", None),
        "SeriesNumber": series_index,
        "SeriesNumberFloat": float(series_index) if series_index else 0.0,
        "Language": str(getattr(mi, "language", None) or "en"),
        "ImageId": _image_id(content_id),
        "___FileSize": file_size,
        "WordCount": -1,
        "NumShortcovers": chapter_count,
        "VolumeIndex": -1,
        "___NumPages": -1,
        "ReadStatus": 0,
        "___PercentRead": 0,
        "DateLastRead": None,
        "FirstTimeReading": "true",
        "TimeSpentReading": 0,
        "ChapterIDBookmarked": None,
        "RestOfBookEstimate": 0,
        "CurrentChapterEstimate": 0,
        "CurrentChapterProgress": 0,
        "DateCreated": now_local,
        "DateAdded": now_local,
        "___SyncTime": now_utc,
        "___UserID": "kepub_user",
        "IsEncrypted": "true",
        "IsDownloaded": "true",
        "ReadStateSynced": "true",
        "PageProgressDirection": "ltr",
        "FavouritesIndex": -1,
        "Accessibility": -1,
        "EpubType": -1,
        "Monetization": 2,
        "InWishlist": "FALSE",
        "IsSocialEnabled": "true",
        "HideFromHomePage": "false",
        "IsInternetArchive": "false",
        "IsPurchaseable": "true",
        "IsSupported": "true",
        "IsAbridged": "false",
        "RedirectPreviewUrl": "false",
        "DownloadUrl": "false",
        "StorePages": 0,
        "StoreWordCount": 0,
        "DateModified": None,
        "WishlistedDate": None,
    }


def _chapter_row(
    book_path: str,
    content_id: str,
    title: str,
    index: int,
    path: str,
    word_count: int,
    size: float,
    offset: int,
) -> dict[str, Any]:
    return {
        "ContentID": f"{book_path}!!{path}",
        "ContentType": "9",
        "MimeType": XHTML_MIME,
        "BookID": content_id,
        "BookTitle": title,
        "Title": path,
        "WordCount": word_count,
        "VolumeIndex": index,
        "Depth": 0,
        "___FileOffset": offset,
        "___FileSize": size,
        "___NumPages": -1,
        "ReadStatus": 0,
        "___PercentRead": 0,
        "DateLastRead": None,
        "ChapterIDBookmarked": None,
        "FirstTimeReading": "true",
        "TimeSpentReading": 0,
        "___UserID": "",
        "IsEncrypted": "false",
        "IsDownloaded": 1,
        "ReadStateSynced": "false",
        "FavouritesIndex": -1,
        "Accessibility": -1,
        "EpubType": -1,
        "Monetization": 2,
        "InWishlist": "FALSE",
        "IsSocialEnabled": "true",
        "IsInternetArchive": "FALSE",
        "IsPurchaseable": "true",
        "IsSupported": "true",
        "StorePages": 0,
        "StoreWordCount": 0,
        "DateModified": None,
        "WishlistedDate": None,
        "DateCreated": None,
        "DateAdded": None,
        "___SyncTime": None,
        "CurrentChapterProgress": 0,
    }


def _toc_row(
    book_path: str,
    content_id: str,
    title: str,
    index: int,
    path: str,
    toc_title: str,
    depth: int,
    chapter_id: Optional[str],
) -> dict[str, Any]:
    return {
        "ContentID": f"{book_path}!!{path}-{depth}",
        "ContentType": "899",
        "MimeType": KEPUB_MIME,
        "BookID": content_id,
        "BookTitle": title,
        "Title": toc_title or path,
        "WordCount": -1,
        "VolumeIndex": index,
        "Depth": depth,
        "___FileOffset": 0,
        "___FileSize": 0,
        "___NumPages": -1,
        "ReadStatus": 0,
        "___PercentRead": 0,
        "DateLastRead": None,
        "ChapterIDBookmarked": chapter_id,
        "FirstTimeReading": "true",
        "TimeSpentReading": 0,
        "___UserID": "",
        "IsEncrypted": "false",
        "IsDownloaded": 1,
        "ReadStateSynced": "false",
        "FavouritesIndex": -1,
        "Accessibility": -1,
        "EpubType": -1,
        "Monetization": 2,
        "InWishlist": "FALSE",
        "IsSocialEnabled": "true",
        "IsInternetArchive": "FALSE",
        "IsPurchaseable": "true",
        "IsSupported": "true",
        "StorePages": 0,
        "StoreWordCount": 0,
        "DateModified": None,
        "WishlistedDate": None,
        "DateCreated": None,
        "DateAdded": None,
        "___SyncTime": None,
        "CurrentChapterProgress": 0,
    }


def _insert_structure(
    driver: Any,
    content_id: str,
    device_name: str,
    mi: Optional[Metadata],
    structure: KepubStructure,
    local_path: str,
) -> Optional[str]:
    title = _book_title(device_name, mi)
    book_path = _book_path(content_id)
    file_size = os.path.getsize(local_path)
    now_local = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with driver.database_transaction() as connection:
        existing = connection.execute(
            "SELECT 1 FROM content WHERE ContentID = ? AND ContentType = '6'",
            (content_id,),
        ).fetchone()
        if existing:
            common.log.info(
                f"Kobo page-count fix skipped for '{title}': book already exists in the Kobo database"
            )
            driver._log_and_show_message(
                f'Page-count fix skipped for "{title}": delete and re-send it to rebuild the page counts',
                4000,
                log_level="info",
            )
            return None
        if not _table_exists(connection, "volume_shortcovers"):
            common.log.warning("Kobo page-count fix: volume_shortcovers table not found")
            return None
        columns = _content_columns(connection)
        _insert_content_row(
            connection,
            columns,
            _book_row(
                content_id,
                title,
                mi,
                file_size,
                len(structure.spine),
                now_local,
                now_utc,
            ),
        )
        chapter_paths: dict[str, str] = {}
        for index, path in enumerate(structure.spine):
            chapter_id = f"{book_path}!!{path}"
            chapter_paths[path] = chapter_id
            _insert_content_row(
                connection,
                columns,
                _chapter_row(
                    book_path,
                    content_id,
                    title,
                    index,
                    path,
                    structure.counts[index],
                    structure.sizes[index],
                    structure.offsets[index],
                ),
            )
        unquoted_chapters = {
            unquote(path): chapter_id for path, chapter_id in chapter_paths.items()
        }
        seen_toc: set[str] = set()
        toc_index = 0
        for entry in structure.toc:
            chapter_id = chapter_paths.get(entry.path) or unquoted_chapters.get(
                unquote(entry.path)
            )
            if chapter_id is None:
                common.log.debug(
                    f"TOC entry '{entry.path}' does not match a spine item; skipping"
                )
                continue
            toc_path = chapter_id.split("!!", 1)[-1]
            toc_id = f"{book_path}!!{toc_path}-{entry.depth}"
            if toc_id in seen_toc:
                common.log.debug(f"Duplicate TOC entry '{toc_id}' skipped")
                continue
            seen_toc.add(toc_id)
            _insert_content_row(
                connection,
                columns,
                _toc_row(
                    book_path,
                    content_id,
                    title,
                    toc_index,
                    toc_path,
                    entry.title,
                    entry.depth,
                    chapter_id,
                ),
            )
            toc_index += 1
        if toc_index == 0:
            raise RuntimeError("no TOC entry matches the KEPUB spine")
        connection.execute(
            "DELETE FROM volume_shortcovers WHERE volumeId = ?", (content_id,)
        )
        connection.executemany(
            "INSERT OR REPLACE INTO volume_shortcovers "
            "(volumeId, shortcoverId, VolumeIndex) VALUES (?, ?, ?)",
            [
                (content_id, f"{book_path}!!{path}", index)
                for index, path in enumerate(structure.spine)
            ],
        )
    common.log.info(
        f"Pre-created Kobo page counts for '{title}' "
        f"({len(structure.spine)} chapters, {toc_index} TOC entries)"
    )
    driver._log_and_show_message(
        f'Pre-created page counts for "{title}" ({len(structure.spine)} chapters)',
        3000,
        log_level="info",
    )
    return content_id


def insert_db_first_book(
    driver: Any, device_name: str, mi: Optional[Metadata]
) -> Optional[str]:
    """Create the complete Kobo database structure for a newly uploaded KEPUB."""
    if driver.isTolinoDevice():
        return None
    if not str(device_name).lower().endswith((".kepub", ".kepub.epub")):
        common.log.debug(f"Kobo page-count fix skipped for non-KEPUB upload: {device_name}")
        return None
    try:
        content_id = _normalize_content_id(driver.contentid_from_path(device_name, 6))
    except Exception as e:  # pylint: disable=broad-except
        common.log.debug(f"Could not resolve Kobo ContentID for '{device_name}': {e}")
        return None
    if not content_id:
        return None
    local_path = driver._device_path_from_contentid(content_id, KEPUB_MIME, None)
    if not local_path or not os.path.isfile(local_path):
        common.log.warning(f"Kobo page-count fix: local file not found for '{content_id}'")
        return None
    structure = read_structure(local_path)
    if structure is None:
        title = _book_title(device_name, mi)
        common.log.warning(
            f"Kobo page-count fix skipped for '{title}': could not read the KEPUB structure "
            "(missing spine or TOC)"
        )
        driver._log_and_show_message(
            f'Page-count fix skipped for "{title}": could not read its KEPUB structure',
            4000,
            log_level="warning",
        )
        return None
    return _insert_structure(driver, content_id, device_name, mi, structure, local_path)


def insert_db_first_books(
    driver: Any,
    result: Any,
    metadata: Optional[List[Metadata]],
    on_card: bool,
) -> None:
    """Apply the DB-first page count fix to the uploaded books."""
    if on_card:
        common.log.info("Kobo page-count fix is only available for books on the main memory")
        return
    if not result:
        return
    if metadata and len(metadata) == len(result):
        aligned_metadata: List[Optional[Metadata]] = list(metadata)
    else:
        if metadata:
            common.log.warning(
                "Kobo page-count fix: metadata count does not match the upload result; "
                "using file-name metadata instead"
            )
        aligned_metadata = [None] * len(result)
    for index, entry in enumerate(result):
        try:
            device_name = entry[0]
        except (TypeError, IndexError):
            continue
        mi = aligned_metadata[index]
        try:
            insert_db_first_book(driver, device_name, mi)
        except Exception as e:  # pylint: disable=broad-except
            common.log.error(
                f"Could not pre-create Kobo page counts for '{device_name}': {e}"
            )
            driver._log_and_show_message(
                f'Page-count fix failed for "{_book_title(device_name, mi)}": {e}',
                5000,
                log_level="warning",
            )


def cleanup_deleted_books(driver: Any, paths: List[str]) -> None:
    """Remove the volume spine rows created by the page-count fix for deleted books."""
    content_ids: List[str] = []
    for raw_path in paths or []:
        try:
            path = driver.normalize_path(raw_path)
            if os.path.exists(path):
                continue
            extension = os.path.splitext(path)[1]
            content_type = (
                driver.get_content_type_from_extension(extension)
                if extension
                else driver.get_content_type_from_path(path)
            )
            content_id = driver.contentid_from_path(path, content_type)
            content_id = _normalize_content_id(content_id)
        except Exception as e:  # pylint: disable=broad-except
            common.log.debug(f"Could not resolve deleted book path '{raw_path}': {e}")
            continue
        if content_id:
            content_ids.append(content_id)
            common.log.debug(
                f"Kobo page-count cleanup: '{raw_path}' -> '{content_id}'"
            )
    if not content_ids:
        return
    deleted: List[str] = []
    with driver.database_transaction() as connection:
        if not _table_exists(connection, "volume_shortcovers"):
            return
        for content_id in content_ids:
            still_present = connection.execute(
                "SELECT 1 FROM content WHERE ContentID = ? OR BookID = ? LIMIT 1",
                (content_id, content_id),
            ).fetchone()
            if still_present is not None:
                common.log.debug(
                    f"Kobo page-count cleanup skipped for '{content_id}': "
                    "book is still in the Kobo database"
                )
                continue
            deleted.append(content_id)
        if not deleted:
            return
        placeholders = ",".join("?" for _ in deleted)
        connection.execute(
            f"DELETE FROM volume_shortcovers WHERE volumeId IN ({placeholders})",
            deleted,
        )
    common.log.info(
        f"Removed {len(deleted)} deleted book(s) from the Kobo page-count spine"
    )
