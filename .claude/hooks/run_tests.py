#!/usr/bin/env python3
"""PostToolUse hook：Claude 用 Edit / Write 改完 app/ 底下的 .py 檔後，自動跑測試。

Hook 是 harness 的一部分，由 Claude Code 執行，不是由模型決定要不要做：
  - 輸入：stdin 上的一個 JSON（含 tool_name、tool_input 等）
  - exit 0：一切正常
  - exit 2：把 stderr 的內容回饋給 Claude

涵蓋範圍要看清楚：
  - settings.json 的 matcher 是 Edit|Write，用 Bash（sed、重導向…）改檔不會觸發。
  - PostToolUse 發生在修改「之後」：exit 2 不會撤銷修改，只是讓 Claude 看到失敗；
    要不要修、修不修得好，仍然是模型的事。想「沒過就不准結束」，要用 Stop hook 當驗收關卡。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

event = json.load(sys.stdin)
file_path = event.get("tool_input", {}).get("file_path", "")

project = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
app_dir = project / "app"

if not file_path.endswith(".py") or app_dir not in Path(file_path).resolve().parents:
    sys.exit(0)

result = subprocess.run(
    [sys.executable, "-m", "unittest", "discover", "-s", str(app_dir), "-q"],
    capture_output=True, text=True, cwd=project,
)

if result.returncode != 0:
    print("❌ 自動測試失敗（由 PostToolUse hook 執行），請修正後再繼續：\n"
          + result.stderr[-3000:], file=sys.stderr)
    sys.exit(2)

print("✅ 自動測試通過")
sys.exit(0)
