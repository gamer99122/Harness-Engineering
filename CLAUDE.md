# Todo CLI 學習專案

<!-- 這份檔案就是 Context：Claude Code 每次在這個資料夾啟動時，都會自動讀進來。
     寫在這裡的東西，Claude 不用問就知道。保持精簡：每一行都會佔用每一次對話的 context。 -->

## 專案結構
- `app/todo.py`：待辦事項 CLI（只用 Python 標準庫）
- `app/test_todo.py`：unittest 測試
- `mcp_servers/todo_stats.py`：自製的 MCP server（設定在 `.mcp.json`）
- 資料存在專案根目錄的 `todos.json`，可用環境變數 `TODO_DB` 改位置

## 常用指令
- 列出：`python3 app/todo.py list`
- 新增：`python3 app/todo.py add "標題"`
- 完成：`python3 app/todo.py done <id>`
- 測試：`python3 -m unittest discover -s app -v`

## 程式慣例
- 只用 Python 標準庫，不要加第三方套件
- 業務邏輯寫成不做檔案 I/O 的函式（只操作傳入的 list），檔案讀寫集中在 `main()`
- 使用者看得到的訊息一律用繁體中文
- 每個新功能都要有測試

## Harness 規則（部分由 hooks 自動檢查）
- 用 Edit/Write 修改 `app/*.py` 後會自動跑測試；收到失敗訊息時，先修好再繼續
- 禁止遞迴刪除，也不要直接修改 `todos.json`（請透過 CLI）。hook 只擋常見寫法，沒被擋不代表允許

## 給 Claude 的額外指示
使用者正在學習 Claude Code 與 harness engineering。每次完成任務後，用一兩句話說明
這次用到了哪些機制（CLAUDE.md / Skill / MCP / Hook / Subagent / Permission），幫助使用者理解。
