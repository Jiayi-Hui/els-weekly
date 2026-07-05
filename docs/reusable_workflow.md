# Reusable Workflow

这份文档记录本次已经跑通的微信群聊周报流程。目标是下次复用时少踩坑，同时避免把私密数据误传到 GitHub。

## 1. 输入与边界

输入通常有三类：

- 微信群聊：不可重新下载的文本、发言者、时间顺序。
- 附件目录：PDF、DOCX、图片、截图，通常可以从本地目录读取。
- 公开信息：公告、公司官网、监管文件、权威媒体、官方产品文档。

边界：

- 不解密微信数据库。
- 不使用 Frida/hook。
- 不发送消息、不点击链接、不自动回复。
- 只采集用户已打开并可见的聊天窗口。
- 所有 OCR 在本机完成。

## 2. 推荐目录结构

```text
tools/wechat_ui_harvester/
  capture_window.py        # 找微信窗口并截图
  ocr_image.py             # macOS Vision OCR
  harvest_chat.py          # 截图 + OCR + 滚动
  reocr_captures.py        # 用新裁剪比例重 OCR 旧截图
  extract_attachments.py   # PDF/DOCX/图片统一抽文本
  README.md

docs/
  reusable_workflow.md
  github_publish_checklist.md

output/                    # 忽略，不提交
tmp/                       # 忽略，不提交
tools/wechat_ui_harvester/captures/ # 忽略，不提交
tools/wechat_ui_harvester/output/   # 忽略，不提交
```

## 3. 权限准备

macOS 需要给运行环境授权：

- Screen Recording：用于截取微信窗口。
- Accessibility：用于激活微信窗口和发送滚轮事件。

授权后如果仍然失败，退出并重新打开 Codex 或 Terminal。

## 4. 采集流程

### 4.1 手动准备

1. 打开微信。
2. 进入目标群聊。
3. 手动滚动到要开始采集的位置。
4. 确认窗口没有被遮挡。

### 4.2 探测

先跑 3 页，确认滚动方向、裁剪区域和 OCR 行数：

```bash
python3 tools/wechat_ui_harvester/harvest_chat.py \
  --pages 3 \
  --direction newer \
  --scroll 32 \
  --crop 0.20,0.06,0.02,0.32 \
  --output tools/wechat_ui_harvester/output/probe.jsonl \
  --overwrite
```

如果方向反了，切换 `--direction older`，或直接调整 `--scroll` 正负。

### 4.3 正式采集

```bash
python3 tools/wechat_ui_harvester/harvest_chat.py \
  --pages 300 \
  --direction newer \
  --scroll 36 \
  --delay-min 0.8 \
  --delay-max 1.5 \
  --crop 0.20,0.06,0.02,0.32 \
  --stop-after-stable-pages 4 \
  --stop-after-duplicate-pages 6 \
  --output tools/wechat_ui_harvester/output/chat_full.jsonl \
  --overwrite
```

建议：

- `--scroll` 可以比初次小心采集更大，但要保留上下文重叠。
- `--stop-after-stable-pages 4` 用于到最新消息后自动停。
- 正式采集不要开 `--dedupe-lines`，否则可能丢重复短消息。

## 5. 附件抽取

将群内文件和图片统一放到一个本地目录，例如 `/path/to/attachments`。

```bash
python3 tools/wechat_ui_harvester/extract_attachments.py \
  --input-dir /path/to/attachments \
  --output-dir tools/wechat_ui_harvester/output/attachment_text
```

支持：

- PDF：`pdfplumber`
- DOCX：直接解析 `word/document.xml`
- 图片：macOS Vision OCR

输出目录中的文本同样是敏感材料，不要提交。

## 6. 内容整理方法

正式周报建议按这个框架写：

1. 一页结论：本周最大边际变化、下一步验证。
2. 分段梳理与逻辑分层：按时间和主题拆解。
3. 核心主题：每个主题按“讨论判断 -> 附件证据 -> 公开验证 -> 投资含义”组织。
4. 关联聚合与深度讨论：把分散话题合成投资问题。
5. 联网补充与观点构建：只把公开可验证信息写成事实。
6. 下周跟踪清单：明确数据、负责人或验证路径。
7. 资料来源：只列公开来源，除非内部版需要列本地材料。

对外版本应隐藏制作痕迹：

- 不写 OCR 行数。
- 不写截图/OCR/采集方法。
- 不列本地文件路径。
- 不写“群内核心判断”，改成“小组核心判断”或“本周判断”。
- 不暴露原始聊天记录。

## 7. PDF 生成与验收

PDF 生成可以用 ReportLab。验收至少做三件事：

```bash
pdfinfo output/pdf/report.pdf
```

```bash
python3 - <<'PY'
from pypdf import PdfReader
r = PdfReader("output/pdf/report.pdf")
text = "\n".join((p.extract_text() or "") for p in r.pages)
print(len(r.pages), len(text))
PY
```

```bash
mkdir -p tmp/pdfs/report_render
pdftoppm -png -r 140 output/pdf/report.pdf tmp/pdfs/report_render/page
```

然后抽查：

- 封面
- 至少一页图片页
- 至少一页表格页
- 最后一页资料来源

确认没有中文缺字、图片裁切、表格溢出、空白页、制作痕迹泄漏。

## 8. 清理策略

可以安全删除：

- `tmp/pdfs/`
- 渲染检查 PNG
- 中间 probe 输出

谨慎删除：

- `tools/wechat_ui_harvester/captures/`

删除截图后不能重新 OCR 或回看原图。若 PDF 已定稿、OCR 文本已足够、且隐私优先，可以删除。
