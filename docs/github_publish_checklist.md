# GitHub Publish Checklist

这个项目涉及私密聊天截图和 OCR 文本。推到 GitHub 前，先跑完下面检查。

## Recommended Visibility

建议优先使用 private repository。

如果要 public repository，只推通用工具和流程文档，不推任何本次聊天/周报内容。

## Files Safe To Commit

```bash
git add .gitignore README.md requirements.txt docs \
  tools/wechat_ui_harvester/README.md \
  tools/wechat_ui_harvester/capture_window.py \
  tools/wechat_ui_harvester/ocr_image.py \
  tools/wechat_ui_harvester/harvest_chat.py \
  tools/wechat_ui_harvester/reocr_captures.py \
  tools/wechat_ui_harvester/extract_attachments.py
```

Do not use `git add -f` unless you are certain the file is sanitized.

## Pre-Commit Checks

Check ignored files:

```bash
git status --short --ignored
```

Look for accidentally staged private data:

```bash
git diff --cached --name-only
```

Check for large files:

```bash
find . -type f -size +10M -not -path './.git/*' -print
```

Search for project/private names before public release:

```bash
rg -n "PRIVATE_GROUP_NAME|PRIVATE_PERSON_NAME|LOCAL_USER_NAME|微信图片|chat_full|project_codename" .
```

This search may match docs intentionally. For a public repo, remove or generalize anything that identifies a private group, person, local path, or client project.

## First Push

```bash
git init
git branch -M main
git add .gitignore README.md requirements.txt docs \
  tools/wechat_ui_harvester/README.md \
  tools/wechat_ui_harvester/capture_window.py \
  tools/wechat_ui_harvester/ocr_image.py \
  tools/wechat_ui_harvester/harvest_chat.py \
  tools/wechat_ui_harvester/reocr_captures.py \
  tools/wechat_ui_harvester/extract_attachments.py
git commit -m "Add reusable WeChat report workflow"
git remote add origin git@github.com:<your-user>/<your-repo>.git
git push -u origin main
```

## Files To Keep Local

- `output/`
- `tmp/`
- `.project-director/`
- `tools/wechat_ui_harvester/captures/`
- `tools/wechat_ui_harvester/output/`
- report-specific generators that include real content
- any chatlog/frida experiment artifacts
