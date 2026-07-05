# WeChat UI Harvester

This is a local, low-intrusion fallback for collecting visible WeChat chat text when database key extraction is not available.

It does not decrypt the WeChat database. It captures the visible WeChat window, crops the chat area, runs macOS Vision OCR locally, then scrolls the current chat.

## Safety boundary

- It only activates WeChat and sends scroll wheel events.
- It does not type, send messages, click links, add contacts, or use Frida/hooks.
- Output files contain private chat text and screenshots. Treat `output/*.jsonl` and `captures/*.png` as sensitive.

## Requirements

Grant Codex or the terminal app:

- System Settings -> Privacy & Security -> Screen Recording
- System Settings -> Privacy & Security -> Accessibility

If capture fails after changing permissions, quit and reopen Codex/Terminal.

## Basic run

Open the target chat in WeChat first, then run:

```bash
python3 tools/wechat_ui_harvester/harvest_chat.py \
  --pages 20 \
  --direction newer \
  --scroll 18 \
  --delay-min 1.0 \
  --delay-max 2.3 \
  --stop-after-stable-pages 4 \
  --stop-after-duplicate-pages 6 \
  --output tools/wechat_ui_harvester/output/chat_run.jsonl
```

Use a small probe first:

```bash
python3 tools/wechat_ui_harvester/harvest_chat.py \
  --pages 3 \
  --direction newer \
  --scroll 18 \
  --output tools/wechat_ui_harvester/output/probe.jsonl \
  --overwrite
```

If the chat moves in the wrong direction, use a negative scroll:

```bash
python3 tools/wechat_ui_harvester/harvest_chat.py --pages 3 --scroll -18 --output tools/wechat_ui_harvester/output/probe.jsonl --overwrite
```

By default the script appends and preserves every OCR row, even if the same short text appears multiple times. Add `--overwrite` to replace the file instead of appending.

For formal capture, keep the default line behavior: every OCR row is preserved, even if the exact same short text appears again. Add `--dedupe-lines` only for rough exploratory runs where losing repeated short messages is acceptable.

## Continue until latest message

When starting from the current chat position and scrolling toward newer messages, use a larger scroll amount plus automatic stop guards:

```bash
python3 tools/wechat_ui_harvester/harvest_chat.py \
  --pages 600 \
  --direction newer \
  --scroll 36 \
  --delay-min 0.8 \
  --delay-max 1.5 \
  --crop 0.20,0.06,0.02,0.32 \
  --segment-pages 100 \
  --stop-after-stable-pages 4 \
  --stop-after-duplicate-pages 6 \
  --output tools/wechat_ui_harvester/output/chat_full.jsonl \
  --overwrite
```

`--stop-after-stable-pages` stops when consecutive cropped screenshots are byte-identical, which usually means the chat can no longer scroll in that direction. `--stop-after-duplicate-pages` is a looser OCR-based fallback.

`--segment-pages 100` writes `chat_full_part001.jsonl`, `chat_full_part002.jsonl`, and so on. Each page is still flushed immediately, so an interrupted overnight run keeps the completed segment files.

## Attachment extraction

Put downloadable files and images in one directory, then extract text locally:

```bash
python3 tools/wechat_ui_harvester/extract_attachments.py \
  --input-dir /path/to/attachments \
  --output-dir tools/wechat_ui_harvester/output/attachment_text
```

Supported inputs:

- PDF via `pdfplumber`
- DOCX via direct XML extraction
- images via macOS Vision OCR

## Files

- `capture_window.py`: finds and captures the visible WeChat window.
- `ocr_image.py`: runs macOS Vision OCR on an image.
- `harvest_chat.py`: capture + OCR + scroll loop.
- `reocr_captures.py`: re-run OCR from saved full-window screenshots with a new crop.
- `extract_attachments.py`: extract text from PDF/DOCX/image attachments.

## Limitations

- OCR is not a perfect chat export: message boundaries, sender names, timestamps, quoted cards, files, and images may need cleanup.
- Only visible history can be collected, so long histories require many pages.
- WeChat's Accessibility tree does not expose message nodes in this build, so this uses screenshots instead of AX text extraction.
