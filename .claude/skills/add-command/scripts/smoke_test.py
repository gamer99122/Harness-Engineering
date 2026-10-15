#!/usr/bin/env python3
"""端對端冒煙測試：用暫存資料庫實際跑一遍 CLI，不會動到真正的 todos.json。

用法：
    python3 .claude/skills/add-command/scripts/smoke_test.py               # 只跑既有指令
    python3 .claude/skills/add-command/scripts/smoke_test.py rename 1 新標題  # 最後再跑新指令

Skill 可以附帶腳本：Claude 不需要每次重寫這段邏輯，直接執行即可。
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TODO = Path(__file__).resolve().parents[4] / "app" / "todo.py"

# (參數, 預期的 exit code)
CASES = [
    (["add", "冒煙測試"], 0),
    (["list"], 0),
    (["done", "1"], 0),
    (["done", "999"], 1),
]


def main() -> int:
    cases = list(CASES)
    if len(sys.argv) > 1:
        cases.append((sys.argv[1:], 0))

    failed = 0
    with tempfile.TemporaryDirectory() as d:
        env = {**os.environ, "TODO_DB": str(Path(d) / "todos.json")}
        for args, expected in cases:
            r = subprocess.run([sys.executable, str(TODO), *args], capture_output=True, text=True, env=env)
            ok = r.returncode == expected
            failed += not ok
            print(f"{'PASS' if ok else 'FAIL'}  todo {' '.join(args)}  (exit {r.returncode}, 預期 {expected})")
            for line in (r.stdout + r.stderr).splitlines():
                print(f"      {line}")

    print(f"\n{len(cases) - failed}/{len(cases)} 通過")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
