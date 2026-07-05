#!/usr/bin/env python3
import argparse
from datetime import datetime
import json
from pathlib import Path

from capture_window import crop_chat_area
from ocr_image import recognize


def normalize_text(text):
    return " ".join(text.strip().split())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-glob", required=True, help="glob for full-window capture PNGs")
    parser.add_argument("--output", required=True)
    parser.add_argument("--crop-output-dir", default="tools/wechat_ui_harvester/captures/reocr")
    parser.add_argument("--crop", default="0.20,0.06,0.02,0.32")
    parser.add_argument("--min-confidence", type=float, default=0.25)
    args = parser.parse_args()

    input_paths = sorted(Path().glob(args.input_glob))
    if not input_paths:
        raise SystemExit(f"no captures matched: {args.input_glob}")

    crop = tuple(float(part) for part in args.crop.split(","))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    crop_output_dir = Path(args.crop_output_dir)
    crop_output_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    written = 0
    with output.open("w", encoding="utf-8") as f:
        for page, input_path in enumerate(input_paths):
            crop_path = crop_output_dir / f"{input_path.stem}_wide_chat.png"
            crop_info = crop_chat_area(input_path, crop_path, crop)
            rows = [
                row
                for row in recognize(str(crop_path), ["zh-Hans", "zh-Hant", "en-US"])
                if row["confidence"] >= args.min_confidence
            ]
            page_lines = 0
            for row_index, row in enumerate(rows):
                text = normalize_text(row["text"])
                if not text:
                    continue
                record = {
                    "run_id": run_id,
                    "source_capture": str(input_path),
                    "page": page,
                    "row_index": row_index,
                    "text": text,
                    "confidence": row["confidence"],
                    "box": row["box"],
                    "crop": crop_info,
                    "capture": str(crop_path),
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                page_lines += 1
                written += 1
            print(json.dumps({"page": page, "rows": page_lines, "capture": str(crop_path)}, ensure_ascii=False), flush=True)

    print(json.dumps({"output": str(output), "written_lines": written}, ensure_ascii=False))


if __name__ == "__main__":
    main()
