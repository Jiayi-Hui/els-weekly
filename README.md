# WeChat Discussion Weekly Report Toolkit

本仓库建议只保存“可复用工具链”和“流程文档”，不要保存任何一次运行产生的私密数据。

当前跑通的低侵入路线是：

1. 用 macOS 窗口截图采集当前打开的微信群聊。
2. 用 macOS Vision 在本地 OCR。
3. 对附件目录中的 PDF、DOCX、图片做本地文本抽取/OCR。
4. 将聊天内容、附件材料、公开新闻/公告交叉验证。
5. 生成面向股票基本面研究小组的周报 PDF。

## Safety Boundary

这套流程不解密微信数据库，不使用 Frida hook，不发送消息，不点击链接。它只做：

- 激活微信窗口
- 截取当前可见窗口
- 裁剪聊天区域
- 本地 OCR
- 发送滚轮事件向上/向下翻页

## What To Commit

建议提交：

- `tools/wechat_ui_harvester/capture_window.py`
- `tools/wechat_ui_harvester/ocr_image.py`
- `tools/wechat_ui_harvester/harvest_chat.py`
- `tools/wechat_ui_harvester/reocr_captures.py`
- `tools/wechat_ui_harvester/extract_attachments.py`
- `tools/wechat_ui_harvester/README.md`
- `skills/els-weekly/`
- `docs/`
- `AGENTS.md`
- `.gitignore`
- `requirements.txt`

默认不要提交：

- `tools/wechat_ui_harvester/captures/`
- `tools/wechat_ui_harvester/output/`
- `output/`
- `tmp/`
- 任何微信群截图、OCR 原文、PDF 成品
- 任何带具体群聊内容的 report generator

## Quick Start

1. 给运行终端或 Codex 授权：
   - System Settings -> Privacy & Security -> Screen Recording
   - System Settings -> Privacy & Security -> Accessibility

2. 安装依赖：

```bash
python3 -m pip install -r requirements.txt
```

3. 打开目标微信群，先做 3 页探测：

```bash
python3 tools/wechat_ui_harvester/harvest_chat.py \
  --pages 3 \
  --direction newer \
  --scroll 32 \
  --crop 0.20,0.06,0.02,0.32 \
  --output tools/wechat_ui_harvester/output/probe.jsonl \
  --overwrite
```

4. 正式采集到最新消息：

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
  --output tools/wechat_ui_harvester/output/chat_run.jsonl \
  --overwrite
```

With `--segment-pages 100`, the script writes files like `chat_run_part001.jsonl` and `chat_run_part002.jsonl` while still flushing after every page.

5. 抽取附件目录文本：

```bash
python3 tools/wechat_ui_harvester/extract_attachments.py \
  --input-dir /path/to/attachments \
  --output-dir tools/wechat_ui_harvester/output/attachment_text
```

完整流程见 [docs/reusable_workflow.md](docs/reusable_workflow.md)。
