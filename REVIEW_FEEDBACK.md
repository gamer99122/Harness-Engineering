# Harness Engineering 入門實驗室：審查回饋

審查日期：2026-10-15  
審查者：Codex

## 整體評價

這是一個適合初學者的入門實驗室，教學設計約 8/10。Todo CLI 規模小，能讓學習者把注意力放在 Context、MCP、Skill、Hook 和 Subagent 如何配合。主要需要改善的是：準確說明機制的保障範圍，以及建立可重複、可比較的實驗方法。

本次讀過 README、CLAUDE.md、Todo CLI 與測試、MCP server、Skill 與附帶腳本、Hooks、權限設定及 reviewer 設定。沒有修改原始範例；尚未在 Claude Code 內實測完整互動流程。

## 實際驗證結果

- `python3 -m unittest discover -s app -v`：7 個測試全部通過。
- `python3 .claude/skills/add-command/scripts/smoke_test.py`：4 個案例全部通過。
- 以模擬的 Bash 工具事件，將指令字串送進 `guard.py`。沒有執行這些指令，結果如下：

| 模擬指令 | Guard 結果 |
|---|---|
| `rm -rf app` | 阻擋，exit code 2 |
| `rm --recursive app` | 放行，exit code 0 |
| `tee todos.json` | 放行，exit code 0 |

這些結果驗證的是 guard 對字串的判斷，不代表指令在目前作業系統一定能執行，也不代表 Claude Code 的其他權限層一定會允許它們。

## 值得保留的設計

1. **範例規模合適。** Todo CLI 容易理解，不會讓業務邏輯蓋過 harness 的學習重點。
2. **各機制都有可讀的實作。** 同一個專案串起 Context、MCP、Skill、Hook 和 Subagent，方便對照。
3. **測試資料有隔離。** `TODO_DB` 與暫存目錄讓測試不會弄亂真正的待辦資料。
4. **有漸進揭露的示範。** Skill 將主要流程、參考範例和可執行腳本分開，結構清楚。
5. **學習迴圈方向正確。**「觀察失敗 → 找原因 → 改環境 → 重跑」是整份教材最有價值的部分。

## 建議優先修正的問題

### 1. 「Hook 100% 強制」的說法過度絕對

位置：`README.md` 的機制比較表、Lesson 4，以及 `.claude/hooks/guard.py` 的說明。

Hook 在符合條件時由 Claude Code 自動執行，這確實不同於依賴模型記住文字指示。但保障程度仍取決於：

- Hook 是否啟用、事件與 matcher 是否涵蓋該操作。
- Hook 程式是否正確處理輸入與錯誤。
- 檢查邏輯是否涵蓋不同工具和不同操作方式。
- 該事件究竟能阻擋操作，還是只能在操作後提供回饋。

現有 guard 用正規表示式攔截部分 shell 寫法，能示範機制，但無法完整禁止遞迴刪除或直接修改資料。例如上述模擬中的 `rm --recursive app` 和 `tee todos.json` 都未被阻擋。

**建議：** 將教材描述改成「符合設定條件時自動執行；攔截效果取決於檢查涵蓋範圍」。明確標示 guard 是教學示範，並增加一個練習：找出未涵蓋的操作方式，理解為何 hook 不能單獨代表完整安全邊界。

### 2. 自動跑測試與強制修正需要分開說明

位置：`.claude/settings.json` 的 `PostToolUse` 設定、`.claude/hooks/run_tests.py`、README Lesson 4。

目前測試 hook 的 matcher 是 `Edit|Write`。透過 Bash 修改 `app/*.py` 不會觸發這個 hook，因此「每次改完 app/*.py 都會自動跑測試」比實際實作的範圍更廣。

此外，`PostToolUse` 發生在工具操作成功後。exit code 2 可以把錯誤訊息回饋給 Claude，但不會撤銷已完成的修改，也不能保證模型一定修好。

官方參考：[Claude Code Hooks reference — PostToolUse](https://code.claude.com/docs/en/hooks#posttooluse)。

**建議：** 明確區分三件事：

- 自動執行檢查。
- 將失敗結果回饋給模型。
- 阻止不合格成果被接受。

對入門實驗室，可先精確寫出「透過 Edit/Write 修改 app 下的 Python 檔案時，自動跑測試」。後續再介紹完成前檢查或 CI 如何作為驗收關卡。

### 3. 畢業專題的 reset 方法可能抹掉 harness 改良

位置：`README.md` Lesson 6，第 4 步（本次審查版本約第 227 行）。

教材要求先改良 harness，再執行 `git reset --hard` 回到起點。若 harness 的修改尚未提交，這個操作會連同改良一起丟棄。另外，未指定目標的 `git reset --hard` 回到目前 HEAD，不一定是實驗的初始版本。

**建議：** 定義明確的 baseline，保存改良後的 harness，並只還原需要重做的 app 與資料。可採用分支或 worktree 做對照；至少應列出具體的保存與還原步驟，避免丟失學習成果。

### 4. 「純函式」用語不準確

位置：`app/todo.py` 的函式區塊註解、`CLAUDE.md`、Skill 和 reviewer 的相關指示。

`add()` 會 append 到傳入的 list，`mark_done()` 會修改其中的 dict，因此兩者有對輸入資料的副作用，不是純函式。參考範例中的 `rename()` 也有相同情況。

這種實作對小型 CLI 很合理，也容易測試；需要修正的是術語。

**建議：** 統一改稱「不做檔案 I/O 的業務邏輯函式」。若真的要教純函式，則應讓函式回傳新資料而不修改輸入，並同步調整呼叫端與測試。

### 5. 缺少驗證 harness 改良效果的方法

位置：`README.md` Lesson 6。

目前主要依靠觀察單次執行來判斷改善。模型的表現有變異，一次成功不足以證明某項 harness 修改有效。

**建議：** 為畢業專題補上簡單的對照實驗：固定任務、初始程式與資料、驗收條件、模型及工具版本，記錄 harness 的差異，每種設定重跑幾次。

| 指標 | 原始 harness | 改良 harness |
|---|---|---|
| 驗收成功次數 / 執行次數 | | |
| 人工介入次數 | | |
| 是否漏跑必要測試 | | |
| 是否違反指定慣例 | | |
| 執行耗時 | | |

驗收條件最好事先訂好，避免只憑模型自己的完成宣告判定成功。也不需要每次失敗都增加規則；應先判斷是需求不清楚、測試不足、工具限制，還是流程真的需要調整。

## 建議修訂順序

1. 修正 Hook 與 PostToolUse 的保障範圍說明。
2. 修正畢業專題的保存及還原流程。
3. 統一修正「純函式」用語。
4. 補上最小的對照實驗與紀錄表。

整體架構值得保留。最值得讓初學者帶走的能力，是把期待變成可檢查的條件，並用重複實驗確認環境改動是否有效。
