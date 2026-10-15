"""簡易待辦事項 CLI —— Harness Engineering 學習用的範例專案。

用法：
    python3 app/todo.py add "買牛奶"
    python3 app/todo.py list
    python3 app/todo.py done 1
"""
import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "todos.json"


def db_path() -> Path:
    return Path(os.environ.get("TODO_DB", DEFAULT_DB))


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, todos: list[dict]) -> None:
    path.write_text(json.dumps(todos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---- 業務邏輯：只操作傳入的 list，不做檔案 I/O，方便測試 ----

def add(todos: list[dict], title: str) -> dict:
    next_id = max((t["id"] for t in todos), default=0) + 1
    todo = {"id": next_id, "title": title, "done": False}
    todos.append(todo)
    return todo


def mark_done(todos: list[dict], todo_id: int) -> dict:
    for t in todos:
        if t["id"] == todo_id:
            t["done"] = True
            return t
    raise KeyError(todo_id)


def format_todo(t: dict) -> str:
    mark = "x" if t["done"] else " "
    return f"[{mark}] {t['id']}. {t['title']}"


# ---- CLI 進入點：負責解析參數與檔案讀寫 ----

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="todo", description="簡易待辦事項")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="新增待辦")
    p_add.add_argument("title")

    sub.add_parser("list", help="列出所有待辦")

    p_done = sub.add_parser("done", help="標記完成")
    p_done.add_argument("id", type=int)

    args = parser.parse_args(argv)
    path = db_path()
    todos = load(path)

    if args.command == "add":
        t = add(todos, args.title)
        save(path, todos)
        print(f"已新增：{format_todo(t)}")
    elif args.command == "list":
        if not todos:
            print("（沒有待辦事項）")
        for t in todos:
            print(format_todo(t))
    elif args.command == "done":
        try:
            t = mark_done(todos, args.id)
        except KeyError:
            print(f"找不到 id={args.id} 的待辦", file=sys.stderr)
            return 1
        save(path, todos)
        print(f"完成：{format_todo(t)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
