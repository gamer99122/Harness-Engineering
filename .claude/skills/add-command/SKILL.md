---
name: add-command
description: 為 todo CLI（app/todo.py）新增子指令的標準流程，包含實作、測試與冒煙測試。當使用者想替 todo 加新功能或新指令（例如 delete、rename、優先順序、清除已完成）時使用。
---

# 為 todo CLI 新增子指令

照順序做，每一步完成再進下一步。

1. **讀現況**：先讀 `app/todo.py` 和 `app/test_todo.py`，理解現有的 `add` / `done` 怎麼寫。
2. **寫業務邏輯函式**：在「業務邏輯」區塊新增函式，只操作傳入的 `list[dict]`，不做檔案 I/O。
   找不到目標時 `raise KeyError`，跟 `mark_done` 一致。
3. **接上 CLI**：在 `main()` 用 `sub.add_parser(...)` 註冊子指令，`help` 用繁體中文；
   在 `if/elif` 分支呼叫業務邏輯函式、`save()`、印出結果。錯誤訊息印到 stderr 並 `return 1`。
4. **寫測試**：在 `app/test_todo.py` 至少加
   - 一個業務邏輯函式的正常情況
   - 一個錯誤情況（例如 id 不存在）
   - 一個透過 `run_cli(...)` 的端對端測試
5. **跑單元測試**：`python3 -m unittest discover -s app -v`
6. **跑冒煙測試**：`python3 .claude/skills/add-command/scripts/smoke_test.py <新指令> <參數...>`
   這支腳本會用暫存資料庫跑過既有指令，最後跑你給的新指令。
7. **更新 context**：在 `CLAUDE.md` 的「常用指令」補上新指令的用法。

需要完整的參考範例時，讀 [examples.md](examples.md)（以 `rename` 指令為例）。
