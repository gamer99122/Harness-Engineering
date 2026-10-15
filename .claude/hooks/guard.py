#!/usr/bin/env python3
"""PreToolUse hook：在工具「執行之前」攔截，擋掉這個專案不允許的動作。

跟寫在 CLAUDE.md 裡的「請不要…」不同，hook 由 Claude Code 自動執行，不靠模型記得：
exit 2 會直接阻止這次工具呼叫，並把 stderr 的理由告訴 Claude。

注意：這是教學示範。hook「一定會執行」，但「擋不擋得住」取決於下面的檢查寫得多完整。
這裡只用正規表示式比對指令字串，會漏擋（換個寫法就過了），也會誤擋（字串裡剛好出現
rm -r 就被擋）。找出漏洞是 README Lesson 4 的練習。
"""
import json
import re
import sys

event = json.load(sys.stdin)
tool = event.get("tool_name", "")
tool_input = event.get("tool_input", {})


def block(reason: str) -> None:
    print(f"🚫 被專案 hook 擋下：{reason}", file=sys.stderr)
    sys.exit(2)


if tool == "Bash":
    command = tool_input.get("command", "")
    if re.search(r"\brm\s+(-\w+\s+)*-\w*[rR]", command):
        block("這個專案禁止遞迴刪除（rm -r）。如果真的需要，請使用者自己執行。")
    if re.search(r">\s*\S*todos\.json", command):
        block("不要用 shell 直接覆寫 todos.json，請透過 `python3 app/todo.py` 操作資料。")

if tool in ("Edit", "Write") and tool_input.get("file_path", "").endswith("todos.json"):
    block("todos.json 是資料檔，請透過 `python3 app/todo.py` 操作，不要直接編輯。")

sys.exit(0)
