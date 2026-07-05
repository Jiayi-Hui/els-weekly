#!/usr/bin/env python3
import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pdfplumber

from ocr_image import recognize


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}


def clean(text):
    text = text or ""
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf(path):
    chunks = []
    with pdfplumber.open(path) as pdf:
        for idx, page in enumerate(pdf.pages, 1):
            text = clean(page.extract_text() or "")
            chunks.append(f"\n--- page {idx} ---\n{text}")
    return clean("\n".join(chunks))


def extract_docx(path):
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    for para in root.findall(".//w:p", ns):
        parts = []
        for node in para.findall(".//w:t", ns):
            if node.text:
                parts.append(node.text)
        line = clean("".join(parts))
        if line:
            paragraphs.append(line)
    return clean("\n".join(paragraphs))


def extract_image(path, min_confidence):
    rows = [row for row in recognize(str(path), ["zh-Hans", "zh-Hant", "en-US"]) if row["confidence"] >= min_confidence]
    return clean("\n".join(row["text"] for row in rows)), rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", default="tools/wechat_ui_harvester/output/attachment_text")
    parser.add_argument("--min-confidence", type=float, default=0.25)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    for path in sorted(p for p in input_dir.iterdir() if p.is_file()):
        suffix = path.suffix.lower()
        status = "ok"
        error = ""
        text = ""
        ocr_rows = None
        try:
            if suffix == ".pdf":
                kind = "pdf"
                text = extract_pdf(path)
            elif suffix == ".docx":
                kind = "docx"
                text = extract_docx(path)
            elif suffix in IMAGE_EXTS:
                kind = "image"
                text, ocr_rows = extract_image(path, args.min_confidence)
            else:
                kind = "unknown"
                status = "skipped"
        except Exception as exc:
            kind = suffix.lstrip(".") or "unknown"
            status = "error"
            error = str(exc)

        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", path.stem).strip("_") or "source"
        text_path = output_dir / f"{safe_name}.txt"
        if status == "ok":
            text_path.write_text(text, encoding="utf-8")
            if ocr_rows is not None:
                (output_dir / f"{safe_name}.ocr.json").write_text(json.dumps(ocr_rows, ensure_ascii=False, indent=2), encoding="utf-8")

        manifest.append(
            {
                "file": str(path),
                "kind": kind,
                "status": status,
                "text_path": str(text_path) if status == "ok" else "",
                "chars": len(text),
                "error": error,
            }
        )

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"manifest": str(manifest_path), "items": manifest}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
