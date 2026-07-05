#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import Quartz
from PIL import Image


def get_wechat_windows():
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionAll, Quartz.kCGNullWindowID)
    out = []
    for window in windows:
        owner = window.get("kCGWindowOwnerName", "") or ""
        name = window.get("kCGWindowName", "") or ""
        bounds = window.get("kCGWindowBounds") or {}
        layer = int(window.get("kCGWindowLayer", 0) or 0)
        onscreen = bool(window.get("kCGWindowIsOnscreen", False))
        if owner not in {"微信", "WeChat"} and "微信" not in name and "WeChat" not in owner:
            continue
        width = int(bounds.get("Width", 0) or 0)
        height = int(bounds.get("Height", 0) or 0)
        if layer != 0 or width < 300 or height < 300:
            continue
        out.append(
            {
                "id": int(window.get("kCGWindowNumber")),
                "owner": owner,
                "name": name,
                "onscreen": onscreen,
                "bounds": {
                    "x": int(bounds.get("X", 0) or 0),
                    "y": int(bounds.get("Y", 0) or 0),
                    "width": width,
                    "height": height,
                },
                "area": width * height,
            }
        )
    out.sort(key=lambda w: (w["onscreen"], w["area"]), reverse=True)
    return out


def save_cgimage(cgimage, path):
    url = Quartz.CFURLCreateFromFileSystemRepresentation(None, str(path).encode(), len(str(path)), False)
    dest = Quartz.CGImageDestinationCreateWithURL(url, "public.png", 1, None)
    Quartz.CGImageDestinationAddImage(dest, cgimage, None)
    if not Quartz.CGImageDestinationFinalize(dest):
        raise RuntimeError(f"failed to write {path}")


def capture_window(window_id, output):
    image = Quartz.CGWindowListCreateImage(
        Quartz.CGRectNull,
        Quartz.kCGWindowListOptionIncludingWindow,
        window_id,
        Quartz.kCGWindowImageBoundsIgnoreFraming,
    )
    if image is None:
        raise RuntimeError("window capture failed; check Screen Recording permission")
    save_cgimage(image, output)


def crop_chat_area(input_path, output_path, crop):
    image = Image.open(input_path)
    width, height = image.size
    left = int(width * crop[0])
    top = int(height * crop[1])
    right = int(width * (1.0 - crop[2]))
    bottom = int(height * (1.0 - crop[3]))
    if right <= left or bottom <= top:
        raise ValueError("invalid crop ratios")
    image.crop((left, top, right, bottom)).save(output_path)
    return {"left": left, "top": top, "right": right, "bottom": bottom, "width": right - left, "height": bottom - top}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="tools/wechat_ui_harvester/captures/window.png")
    parser.add_argument("--crop-output", default="")
    parser.add_argument("--window-id", type=int, default=0)
    parser.add_argument("--list", action="store_true")
    parser.add_argument(
        "--crop",
        default="0.30,0.06,0.02,0.32",
        help="left,top,right,bottom ratios for the chat history area",
    )
    args = parser.parse_args()

    windows = get_wechat_windows()
    if args.list:
        print(json.dumps(windows, ensure_ascii=False, indent=2))
        return
    if not windows and args.window_id == 0:
        raise SystemExit("no WeChat window found")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    window_id = args.window_id or windows[0]["id"]
    capture_window(window_id, output)
    print(json.dumps({"window_id": window_id, "output": str(output), "window": windows[0] if windows else None}, ensure_ascii=False))

    if args.crop_output:
        crop = tuple(float(part) for part in args.crop.split(","))
        crop_output = Path(args.crop_output)
        crop_output.parent.mkdir(parents=True, exist_ok=True)
        info = crop_chat_area(output, crop_output, crop)
        print(json.dumps({"crop_output": str(crop_output), "crop": info}, ensure_ascii=False))


if __name__ == "__main__":
    main()
