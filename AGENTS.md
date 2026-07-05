# Agent Notes

## GitHub Push On This Mac

- Prefer `/usr/bin/git` for GitHub network operations such as `push`, `pull`, `fetch`, and `ls-remote`.
- The Codex-bundled Git may not read macOS `osxkeychain` credentials and can fail with `could not read Username for 'https://github.com'`.
- If a GitHub push fails from the bundled Git, retry with `/usr/bin/git push ...` before changing remotes or asking for new credentials.

## Commit Safety

- Do not use `git add .` in this repository.
- Stage files explicitly by whitelist.
- Never commit screenshots, OCR originals, generated PDFs, private chat exports, report-specific generators, Frida experiments, or ChatLog experiment files unless the user explicitly asks after a privacy review.
