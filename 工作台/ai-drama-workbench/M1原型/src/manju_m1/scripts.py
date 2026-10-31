"""Pure TXT/DOCX extraction, independent of Streamlit and SQLite."""
from dataclasses import dataclass
from io import BytesIO
from pathlib import PureWindowsPath
from zipfile import ZipFile

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_DOCX_EXPANDED_BYTES = 30 * 1024 * 1024


class ScriptReadError(ValueError):
    """An expected, user-readable import failure."""


@dataclass(frozen=True)
class ParsedScript:
    text: str
    source_type: str
    encoding: str
    warning: str = ""


def display_filename(filename: str) -> str:
    # A browser filename is display metadata, never a storage destination.
    return PureWindowsPath(filename).name[:240]


def _normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if any(ord(c) < 32 and c not in "\n\t\f" for c in text):
        raise ScriptReadError("文件包含异常控制字符，请确认它是真实文本并选择正确编码。")
    if not text.strip():
        raise ScriptReadError("剧本没有可读取的正文。")
    return text


def _read_txt(data: bytes, encoding: str | None) -> ParsedScript:
    if encoding is None:
        if data.startswith((b"\xff\xfe", b"\xfe\xff")):
            encodings = ["utf-16"]
        else:
            encodings = ["utf-8-sig", "gb18030"]
    else:
        if encoding not in {"utf-8-sig", "gb18030", "utf-16"}:
            raise ScriptReadError("不支持的文本编码。")
        encodings = [encoding]
    for candidate in encodings:
        try:
            text = data.decode(candidate, errors="strict")
        except UnicodeError:
            continue
        return ParsedScript(_normalize(text), "txt", candidate)
    raise ScriptReadError("无法按所选编码读取TXT，请尝试UTF-8、GB18030或带BOM的UTF-16。")


def _blocks(container):
    for block in container.iter_inner_content():
        if isinstance(block, Paragraph):
            yield block.text
        elif isinstance(block, Table):
            seen_cells = set()
            for row in block.rows:
                cells = []
                for cell in row.cells:
                    if cell._tc in seen_cells:
                        continue
                    seen_cells.add(cell._tc)
                    cells.append("\n".join(_blocks(cell)))
                if cells:
                    yield "\t".join(cells)


def _read_docx(data: bytes) -> ParsedScript:
    try:
        with ZipFile(BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) > 2000 or sum(e.file_size for e in entries) > MAX_DOCX_EXPANDED_BYTES:
                raise ScriptReadError("DOCX解压后内容过大，请拆分剧本后上传。")
            if "word/document.xml" not in archive.namelist() or any(e.flag_bits & 1 for e in entries):
                raise ScriptReadError("不是可读取的DOCX正文，或文件已加密。")
        document = Document(BytesIO(data))
        text = "\n".join(_blocks(document))
    except ScriptReadError:
        raise
    except Exception as exc:
        raise ScriptReadError("DOCX损坏或格式不受支持，请用Word另存为标准DOCX。") from exc
    return ParsedScript(
        _normalize(text), "docx", "DOCX/XML",
        "按正文顺序读取段落和表格；文本框、页眉页脚、批注、修订及图片文字不保证提取，请对照原件。",
    )


def parse_script(filename: str, data: bytes, encoding: str | None = None) -> ParsedScript:
    if not data:
        raise ScriptReadError("文件为空。")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ScriptReadError("单个剧本最大5MB，请先拆分文件。")
    suffix = PureWindowsPath(filename).suffix.lower()
    if suffix == ".txt":
        return _read_txt(data, encoding)
    if suffix == ".docx":
        return _read_docx(data)
    raise ScriptReadError("仅支持TXT和DOCX；旧版DOC请先另存为DOCX。")