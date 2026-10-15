#!/usr/bin/env python3
"""todo-stats：一個「零依賴」的最小 MCP server，用來看清楚 MCP 到底是什麼。

MCP 的本質其實很單純：
  1. Claude Code 依照專案根目錄的 .mcp.json，把這支程式當成子行程啟動
  2. 雙方透過 stdin / stdout 交換 JSON-RPC 2.0 訊息，一行一個 JSON
  3. Claude 先問「你有哪些工具？」(tools/list)，需要時再呼叫 (tools/call)

注意：stdout 是通訊專用的，除錯訊息一定要印到 stderr，否則會弄壞協定。

實務上通常會用官方 SDK（Python 是 `pip install mcp`）幫你處理這些細節；
這裡手寫，是為了讓你看到底層到底發生了什麼。
"""
import json
import os
import sys
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "todos.json"
DB = Path(os.environ.get("TODO_DB", DEFAULT_DB))

# Claude 只看得到 name / description / inputSchema，
# 所以 description 要寫清楚「這個工具做什麼、什麼時候該用」。
TOOLS = [
    {
        "name": "todo_stats",
        "description": "取得待辦事項統計：總數、已完成、未完成、完成率。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "search_todos",
        "description": "用關鍵字搜尋待辦事項標題（不分大小寫）。",
        "inputSchema": {
            "type": "object",
            "properties": {"keyword": {"type": "string", "description": "要搜尋的關鍵字"}},
            "required": ["keyword"],
        },
    },
]


def load_todos() -> list[dict]:
    if not DB.exists():
        return []
    return json.loads(DB.read_text(encoding="utf-8"))


def todo_stats(_args: dict) -> str:
    todos = load_todos()
    total = len(todos)
    done = sum(1 for t in todos if t["done"])
    rate = f"{done / total:.0%}" if total else "N/A"
    return f"總數 {total}，已完成 {done}，未完成 {total - done}，完成率 {rate}"


def search_todos(args: dict) -> str:
    keyword = args.get("keyword", "").lower()
    hits = [t for t in load_todos() if keyword in t["title"].lower()]
    if not hits:
        return f"找不到包含「{keyword}」的待辦"
    return "\n".join(f"[{'x' if t['done'] else ' '}] {t['id']}. {t['title']}" for t in hits)


HANDLERS = {"todo_stats": todo_stats, "search_todos": search_todos}


class MethodNotFound(Exception):
    pass


def text_result(text: str, is_error: bool = False) -> dict:
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def handle(method: str, params: dict) -> dict:
    if method == "initialize":
        # 握手：告訴 Claude Code 我們支援哪個協定版本、提供哪些能力
        return {
            "protocolVersion": params.get("protocolVersion", "2025-06-18"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "todo-stats", "version": "0.1.0"},
        }
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        handler = HANDLERS.get(params.get("name"))
        if handler is None:
            return text_result(f"未知的工具：{params.get('name')}", is_error=True)
        try:
            return text_result(handler(params.get("arguments") or {}))
        except Exception as e:  # 工具出錯要回報給 Claude，而不是讓整個 server 掛掉
            return text_result(f"執行失敗：{e!r}", is_error=True)
    if method == "ping":
        return {}
    raise MethodNotFound(method)


def main() -> None:
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        if not line.strip():
            continue
        msg = json.loads(line)
        method = msg.get("method")
        print(f"[todo-stats] <- {method}", file=sys.stderr)
        # 沒有 id 的是 notification（例如 notifications/initialized），不需要回覆
        if method is None or "id" not in msg:
            continue
        try:
            reply = {"jsonrpc": "2.0", "id": msg["id"], "result": handle(method, msg.get("params") or {})}
        except MethodNotFound:
            reply = {"jsonrpc": "2.0", "id": msg["id"],
                     "error": {"code": -32601, "message": f"Method not found: {method}"}}
        print(json.dumps(reply, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
