#!/usr/bin/env python3
import argparse
import json

import objc
from Foundation import NSURL

objc.loadBundle("Vision", globals(), bundle_path="/System/Library/Frameworks/Vision.framework")


def recognize(path, languages):
    request = VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLanguages_(languages)
    request.setUsesLanguageCorrection_(True)
    try:
        request.setRecognitionLevel_(VNRequestTextRecognitionLevelAccurate)
    except Exception:
        pass

    url = NSURL.fileURLWithPath_(path)
    handler = VNImageRequestHandler.alloc().initWithURL_options_(url, {})
    ok = handler.performRequests_error_([request], None)
    if not ok:
        raise RuntimeError("Vision OCR failed")

    rows = []
    for observation in request.results() or []:
        candidates = observation.topCandidates_(1)
        if not candidates:
            continue
        candidate = candidates[0]
        box = observation.boundingBox()
        rows.append(
            {
                "text": str(candidate.string()),
                "confidence": float(candidate.confidence()),
                "box": {
                    "x": float(box.origin.x),
                    "y": float(box.origin.y),
                    "width": float(box.size.width),
                    "height": float(box.size.height),
                },
            }
        )
    rows.sort(key=lambda r: (-r["box"]["y"], r["box"]["x"]))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--min-confidence", type=float, default=0.25)
    parser.add_argument("--languages", default="zh-Hans,zh-Hant,en-US")
    args = parser.parse_args()

    languages = [part.strip() for part in args.languages.split(",") if part.strip()]
    rows = [row for row in recognize(args.image, languages) if row["confidence"] >= args.min_confidence]
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print("\n".join(row["text"] for row in rows))


if __name__ == "__main__":
    main()
