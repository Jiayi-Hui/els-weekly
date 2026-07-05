---
name: els-weekly
description: Build a privacy-preserving weekly research report from a visible WeChat group chat, local attachments, and public-source verification. Use when the user asks to collect WeChat chat history through macOS screenshots/OCR, extract attachment text, synthesize a stock or fundamental-research weekly report, create a polished PDF, or reuse the ELS weekly workflow.
---

# ELS Weekly

## Operating Boundary

Use the low-intrusion path by default:

- Do not decrypt WeChat databases, use Frida/hook, fetch WeChat keys, send messages, click links, add contacts, or auto-reply.
- Only capture a user-opened visible WeChat window, OCR it locally with macOS Vision, and scroll the current chat.
- Treat screenshots, JSONL/TXT OCR, attachments, generated PDFs, and report-specific generators as private artifacts. Never commit them without an explicit privacy review.

## Workflow

1. Inspect the repo and read `AGENTS.md` if present.
2. Confirm macOS permissions for the running app: Screen Recording and Accessibility.
3. Ask the user to open the target chat and manually position it at the earliest message to collect.
4. Run a short probe before long collection:

```bash
python3 tools/wechat_ui_harvester/harvest_chat.py \
  --pages 3 \
  --direction newer \
  --scroll 32 \
  --crop 0.20,0.06,0.02,0.32 \
  --output tools/wechat_ui_harvester/output/probe.jsonl \
  --overwrite
```

5. For long runs, use segmented JSONL output and automatic stop guards:

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

This creates files such as `chat_full_part001.jsonl`, `chat_full_part002.jsonl`, and flushes each page after OCR.

6. Extract local attachments when supplied:

```bash
python3 tools/wechat_ui_harvester/extract_attachments.py \
  --input-dir /path/to/attachments \
  --output-dir tools/wechat_ui_harvester/output/attachment_text
```

7. Synthesize the report by topic, not by raw chronology:

- Start with a concise weekly judgment and next verification points.
- For each topic, separate discussion judgment, attachment evidence, public verification, and investment implication.
- Use web browsing for current public news, filings, official docs, or other time-sensitive facts; cite sources in the final artifact where appropriate.
- Hide production traces in client-facing PDFs: no OCR line counts, local paths, screenshot method, or internal-processing notes.

8. Verify the PDF visually and textually before delivery. Render pages with Poppler when layout matters and inspect cover, tables, image pages, and final sources.

9. Clean private intermediates only after the user approves. Prefer deleting screenshot caches and render PNGs while keeping the final PDF and intentionally retained JSONL/TXT.

## Git And Publishing

Use whitelist staging. Do not use `git add .`.

On this Mac, prefer `/usr/bin/git` for GitHub network operations because the bundled Git may not read macOS `osxkeychain` credentials.

Safe-to-publish files are reusable code, docs, and this skill. Keep these local unless explicitly sanitized: screenshots, OCR originals, PDF outputs, report-specific generators, Frida experiments, ChatLog experiments, local attachments, and private exports.
