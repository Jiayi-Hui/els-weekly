#!/usr/bin/env python3
import argparse
from datetime import datetime
import hashlib
import json
import random
import subprocess
import sys
import time
from pathlib import Path

import Quartz

from capture_window import crop_chat_area, get_wechat_windows, capture_window
from ocr_image import recognize


def normalize_text(text):
    return " ".join(text.strip().split())


def text_signature(lines):
    joined = "\n".join(normalize_text(line["text"]) for line in lines if normalize_text(line["text"]))
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()


def file_signature(path):
    return hashlib.sha1(path.read_bytes()).hexdigest()


def load_existing_signatures(output):
    signatures = set()
    if not output.exists():
        return signatures
    with output.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                text = normalize_text(json.loads(line).get("text", ""))
            except Exception:
                continue
            if text:
                signatures.add(hashlib.sha1(text.encode("utf-8")).hexdigest())
    return signatures


def activate_wechat():
    script = """
tell application "System Events"
  if exists process "WeChat" then
    tell process "WeChat" to set frontmost to true
  else if exists process "微信" then
    tell process "微信" to set frontmost to true
  end if
end tell
"""
    subprocess.run(["osascript", "-e", script], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def scroll_at(x, y, amount):
    event = Quartz.CGEventCreateScrollWheelEvent(None, Quartz.kCGScrollEventUnitPixel, 1, int(amount))
    Quartz.CGEventSetLocation(event, Quartz.CGPoint(x, y))
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=8)
    parser.add_argument("--output", default="tools/wechat_ui_harvester/output/harvest.jsonl")
    parser.add_argument("--captures-dir", default="tools/wechat_ui_harvester/captures")
    parser.add_argument("--crop", default="0.30,0.06,0.02,0.32")
    parser.add_argument("--scroll", type=int, default=7, help="positive values scroll upward in most WeChat builds")
    parser.add_argument(
        "--direction",
        choices=("older", "newer", "up", "down"),
        default="",
        help="optional direction alias; older/up makes scroll positive, newer/down makes scroll negative",
    )
    parser.add_argument("--delay-min", type=float, default=0.7)
    parser.add_argument("--delay-max", type=float, default=1.8)
    parser.add_argument("--min-confidence", type=float, default=0.25)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true", help="replace the output file instead of appending")
    parser.add_argument(
        "--dedupe-lines",
        action="store_true",
        help="skip OCR lines with the exact same text as earlier rows; off by default to avoid losing repeated real messages",
    )
    parser.add_argument(
        "--stop-after-stable-pages",
        type=int,
        default=0,
        help="stop after this many consecutive captures have the same cropped image as the prior page; useful for stopping at chat bottom/top",
    )
    parser.add_argument(
        "--stop-after-duplicate-pages",
        type=int,
        default=0,
        help="stop after this many consecutive OCR-duplicate pages; useful when the UI is stuck but image bytes are not identical",
    )
    args = parser.parse_args()

    crop = tuple(float(part) for part in args.crop.split(","))
    if args.direction in {"older", "up"}:
        args.scroll = abs(args.scroll)
    elif args.direction in {"newer", "down"}:
        args.scroll = -abs(args.scroll)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    captures_dir = Path(args.captures_dir)
    captures_dir.mkdir(parents=True, exist_ok=True)

    windows = get_wechat_windows()
    if not windows:
        raise SystemExit("no WeChat window found")
    window = windows[0]
    window_id = window["id"]
    bounds = window["bounds"]
    center_x = bounds["x"] + bounds["width"] * 0.68
    center_y = bounds["y"] + bounds["height"] * 0.42

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    seen_pages = set()
    if args.dedupe_lines:
        seen_lines = set() if args.overwrite else load_existing_signatures(output)
    else:
        seen_lines = set()
    written = 0
    last_image_sig = None
    stable_pages = 0
    duplicate_pages = 0
    activate_wechat()
    time.sleep(0.3)

    mode = "w" if args.overwrite else "a"
    with output.open(mode, encoding="utf-8") as f:
        for page in range(args.pages):
            captured_at = datetime.now().isoformat(timespec="seconds")
            full_path = captures_dir / f"page_{run_id}_{page:03d}.png"
            crop_path = captures_dir / f"page_{run_id}_{page:03d}_chat.png"
            capture_window(window_id, full_path)
            crop_info = crop_chat_area(full_path, crop_path, crop)
            image_sig = file_signature(crop_path)
            if image_sig == last_image_sig:
                stable_pages += 1
            else:
                stable_pages = 0
            last_image_sig = image_sig
            rows = [row for row in recognize(str(crop_path), ["zh-Hans", "zh-Hant", "en-US"]) if row["confidence"] >= args.min_confidence]
            sig = text_signature(rows)

            if sig not in seen_pages:
                seen_pages.add(sig)
                duplicate_pages = 0
                page_lines = []
                for row_index, row in enumerate(rows):
                    text = normalize_text(row["text"])
                    if not text:
                        continue
                    line_sig = hashlib.sha1(text.encode("utf-8")).hexdigest()
                    if args.dedupe_lines and line_sig in seen_lines:
                        continue
                    seen_lines.add(line_sig)
                    record = {
                        "run_id": run_id,
                        "page": page,
                        "row_index": row_index,
                        "captured_at": captured_at,
                        "text": text,
                        "confidence": row["confidence"],
                        "box": row["box"],
                        "crop": crop_info,
                        "capture": str(crop_path),
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    page_lines.append(text)
                    written += 1
                f.flush()
                print(
                    json.dumps(
                        {
                            "page": page,
                            "new_lines": len(page_lines),
                            "capture": str(crop_path),
                            "crop": crop_info,
                            "stable_pages": stable_pages,
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
            else:
                duplicate_pages += 1
                print(
                    json.dumps(
                        {
                            "page": page,
                            "duplicate_page": True,
                            "capture": str(crop_path),
                            "stable_pages": stable_pages,
                            "duplicate_pages": duplicate_pages,
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )

            if args.dry_run or page == args.pages - 1:
                break
            if args.stop_after_stable_pages and stable_pages >= args.stop_after_stable_pages:
                print(json.dumps({"stopped": "stable_pages", "count": stable_pages, "page": page}, ensure_ascii=False), flush=True)
                break
            if args.stop_after_duplicate_pages and duplicate_pages >= args.stop_after_duplicate_pages:
                print(json.dumps({"stopped": "duplicate_pages", "count": duplicate_pages, "page": page}, ensure_ascii=False), flush=True)
                break

            jitter = random.uniform(args.delay_min, args.delay_max)
            time.sleep(jitter)
            scroll_amount = args.scroll + random.randint(-2, 2)
            scroll_at(center_x, center_y, scroll_amount)
            time.sleep(random.uniform(0.35, 0.9))

    print(json.dumps({"output": str(output), "written_lines": written}, ensure_ascii=False))


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
