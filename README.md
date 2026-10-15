# Harness Engineering 入門實驗室

用一個很小的 Todo CLI，動手學會 Claude Code 的 **Context、MCP、Skill**，
再把它們串起來，理解什麼是 **Harness Engineering**。

---

## 先建立心智模型：Agent = Model + Harness

模型（Claude）本身只會「讀文字、產生文字」。讓它變成能幫你寫程式的 agent 的，
是包在外面的一整套東西——這套東西叫 **harness**（馬具、安全帶的意思：
用來駕馭一匹很有力但不受控的馬）。Claude Code 本身就是一個 harness。

**Harness Engineering** = 你不改模型，而是設計模型所處的環境，
讓它更穩定地做出你要的結果。Context、MCP、Skill 都是 harness 的零件：

```
┌──────────────────── Harness（你可以工程化的部分）────────────────────┐
│                                                                      │
│  Context     CLAUDE.md、對話、@檔案           → 模型「知道」什麼        │
│  MCP / 工具  內建工具 + .mcp.json             → 模型「能做」什麼        │
│  Skill       .claude/skills/*/SKILL.md       → 模型「怎麼做」（按需載入）│
│  Subagent    .claude/agents/*.md             → 分工、隔離 context      │
│  Permission  settings.json 的 allow / deny   → 「能不能做」            │
│  Hook        settings.json 的 hooks          → 「一定會發生」的事       │
│  回饋迴路    測試、linter、型別檢查             → 模型「知道自己做錯了」   │
│                                                                      │
│                          ↕                                           │
│                    Model（Claude）                                    │
└──────────────────────────────────────────────────────────────────────┘
```

### 最重要的一張表：該把規則放在哪一層？

| 機制 | 何時進入 context | 一定會執行嗎？ | 適合放什麼 |
|---|---|---|---|
| **CLAUDE.md** | 每次對話開始就整份載入 | 否，模型「應該」遵守 | 專案結構、慣例、常用指令 |
| **Skill** | 平常只載入 name + description；用到才讀全文 | 否 | 特定任務的 SOP、範本、附帶腳本 |
| **MCP** | 預設按需載入：用到時才把工具定義搜尋進來 | — | 連接外部系統（DB、GitHub、瀏覽器、內部 API） |
| **Hook** | 不佔 context，由 Claude Code 執行 | **是**：事件與 matcher 對上就一定執行；但擋不擋得住，看檢查寫得多完整 | 不能漏的檢查：跑測試、擋危險指令 |
| **Subagent** | 在獨立的 context 裡跑，只回傳結論 | 否 | 審查、大量搜尋等會塞爆主對話的工作 |

> **核心心法**：「寫在 CLAUDE.md 裡」是**建議**，模型可能忘記；「寫成 hook」是**自動執行**，不靠模型記得。
> 但 hook 只保證「會執行」，能擋住多少，取決於你的檢查涵蓋多少。
> Agent 每犯一次錯，就問自己：這該補在哪一層，讓它下次不會再犯？

---

## 專案地圖

```
.
├── CLAUDE.md                          ← Lesson 1：Context
├── .mcp.json                          ← Lesson 2：MCP 設定
├── mcp_servers/todo_stats.py          ← Lesson 2：零依賴的 MCP server
├── .claude/
│   ├── skills/add-command/            ← Lesson 3：Skill
│   │   ├── SKILL.md                   ←   主要指示（用到才載入）
│   │   ├── examples.md                ←   更細的範例（需要時才讀）
│   │   └── scripts/smoke_test.py      ←   Skill 附帶的腳本
│   ├── settings.json                  ← Lesson 4：Hooks + Permissions
│   ├── hooks/guard.py                 ←   PreToolUse：擋危險動作
│   ├── hooks/run_tests.py             ←   PostToolUse：改完自動跑測試
│   └── agents/reviewer.md             ← Lesson 5：Subagent
└── app/
    ├── todo.py                        ← 練習用的小程式
    └── test_todo.py
```

---

## Lesson 0：準備

需要：Python 3.10 以上、已安裝 [Claude Code](https://docs.claude.com/en/docs/claude-code/overview)。

```bash
git clone https://github.com/gamer99122/Harness-Engineering.git
cd Harness-Engineering
python3 app/todo.py add "學 Context"
python3 app/todo.py add "學 MCP"
python3 app/todo.py add "學 Skill"
python3 app/todo.py done 1
claude
```

clone 下來就已經是 git repo：之後可以用 `git diff` 看 Claude 改了什麼，改壞了用 `git restore` 復原。
`todos.json` 在 `.gitignore` 裡，每個人都從空的待辦清單開始。

啟動時 Claude Code 會問你兩件事，**這本身就是 harness 的一部分**：
- 是否信任這個資料夾（因為 `.claude/settings.json` 裡有 hooks，會執行程式）
- 是否啟用 `.mcp.json` 裡的 `todo-stats` MCP server → 選允許

幾個隨時好用的指令：`/context`（看 context 被什麼佔用）、`/mcp`、`/hooks`、`/skills`、
`/memory`、`/clear`（清空對話）、`/rewind`（回到之前的狀態）。

---

## Lesson 1：Context —— 模型「知道」什麼

**概念**：模型沒有記憶，每次對話都是從零開始。它知道的一切都來自 context：
系統提示、CLAUDE.md、你說的話、它讀過的檔案、工具回傳的結果。
Context 有上限，而且塞越多雜訊，表現越差——所以 context 要「精」不是要「多」。

**動手做**
1. 讀一遍 `CLAUDE.md`。
2. 在 Claude Code 裡問：「這個專案怎麼跑測試？」→ 它不用翻檔案就能回答，因為 CLAUDE.md 已在 context 裡。
3. 輸入 `/context`，看看 CLAUDE.md、工具定義、MCP 各佔了多少 token。
4. 輸入 `/clear` 清空對話，再問一次 → 還是知道。這就是「每次都會載入」。

**練習**
- 在 CLAUDE.md 加一條規則，例如「所有函式都要有一行繁體中文 docstring」，再請 Claude 寫個新函式，觀察它有沒有遵守。
- 想一想：如果它**偶爾**沒遵守怎麼辦？（答案在 Lesson 4）

**延伸**：`~/.claude/CLAUDE.md` 是個人層級的（所有專案都會載入）；子資料夾也可以放 CLAUDE.md；
新專案可以用 `/init` 讓 Claude 幫你產生初版。

---

## Lesson 2：MCP —— 模型「能做」什麼

**概念**：MCP（Model Context Protocol）是讓 Claude 連接外部工具的標準協定。
Claude Code 啟動 MCP server（一個普通程式），透過 stdin/stdout 用 JSON 溝通，
問它「你有哪些工具？」，需要時再呼叫。

**動手做**
1. 輸入 `/mcp`，確認 `todo-stats` 是 connected。
2. 問：「目前待辦完成率多少？」→ 觀察 Claude 呼叫 `todo_stats` 工具（第一次會問你是否允許）。
3. 問：「有哪些待辦跟 Skill 有關？」→ 觀察它呼叫 `search_todos`。
4. **拆開來看**：讀 `mcp_servers/todo_stats.py`（不到 150 行），然後在終端機手動當一次 Claude Code：

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"todo_stats","arguments":{}}}' \
  | python3 mcp_servers/todo_stats.py
```

你會看到三行 JSON 回覆——這就是 MCP 的全部本質。

**練習**
- 請 Claude 幫 MCP server 加一個新工具 `oldest_pending`（回傳 id 最小的未完成項目），重開 `claude` 後測試。
- 注意 `description` 寫得好不好，直接影響 Claude 會不會在對的時機用它。

**延伸**：MCP 真正的價值在連接「Claude 本來碰不到的東西」。試試加一個現成的遠端 MCP：
```bash
claude mcp add --transport http context7 https://mcp.context7.com/mcp   # 查詢最新的套件文件
claude mcp list
```
注意：目前版本的 MCP 工具預設按需載入（`/context` 會顯示 `loaded on-demand · 0 tokens`），裝多一點也不太佔 context；
但工具越多，Claude 越難挑對工具，不用的 server 還是建議移除（`claude mcp remove <name>`）。

---

## Lesson 3：Skill —— 模型「怎麼做」

**概念**：Skill 是一個資料夾，裡面有 `SKILL.md`（＋可選的參考文件、腳本）。
重點是 **progressive disclosure（漸進揭露）**：
- 平常只有 frontmatter 的 `name` + `description` 在 context 裡（很省）
- Claude 判斷任務相關時，才讀 SKILL.md 全文
- SKILL.md 裡提到的 `examples.md`、腳本，又是更需要時才讀/執行

所以 Skill 適合放「很長、但只有特定任務才需要」的知識，不該塞進 CLAUDE.md。

**動手做**
1. 讀 `.claude/skills/add-command/SKILL.md`，特別注意 `description` 怎麼寫。
2. 對 Claude 說：「幫我加一個 delete 指令，可以刪除指定 id 的待辦」
   → 觀察它有沒有自動載入 `add-command` skill，照步驟走、最後跑 smoke_test.py。
3. 也可以直接輸入 `/add-command 加一個 clear-done 指令，清除所有已完成的項目` 手動觸發。

**練習**
- 自己寫一個 skill，例如 `.claude/skills/release-notes/SKILL.md`：讀 `git log` 產生繁體中文的版本說明。
- 故意把 description 寫得很模糊，觀察 Claude 是不是就不會自動用它了。
- 進階：用內建的 `skill-creator` skill 讓 Claude 幫你寫 skill、還能做評測。

---

## Lesson 4：Hooks —— Harness Engineering 的核心

**概念**：Context 和 Skill 都是「給模型看的建議」，模型可能忘記、可能誤判。
Hook 是 **Claude Code 本身在特定時機執行的程式**，不經過模型判斷：只要事件和 matcher 對上，就一定會執行。

但「一定會執行」不等於「一定擋得住」。hook 能保證多少，要看三件事：
- **涵蓋範圍**：matcher 有沒有包含那個工具？檢查邏輯有沒有涵蓋各種寫法？
- **時機**：事件發生在動作之前還是之後，決定它能不能「阻止」。
- **程式本身**：hook 也是程式，也會有 bug。

| 事件 | 什麼時候 | exit 2 的效果 |
|---|---|---|
| `PreToolUse` | 工具執行**前** | 阻止這次工具呼叫，理由回饋給 Claude |
| `PostToolUse` | 工具成功執行**後** | 只能把訊息回饋給 Claude；修改已經發生，不會被撤銷 |
| `Stop` | Claude 準備結束回答時 | 不讓它結束、要它繼續處理——可以當「驗收關卡」 |

這個專案設了兩個 hook（見 `.claude/settings.json`）：
- `PreToolUse` → `guard.py`：工具執行**前**檢查，擋掉常見的 `rm -r` 寫法、直接改 `todos.json`。
  這是**教學示範**，只比對指令字串，並不完整（見下方練習）。
- `PostToolUse` → `run_tests.py`：Claude 用 **Edit / Write** 改完 `app/*.py` 後，**自動**跑測試；
  失敗就用 exit code 2 把錯誤訊息回饋給 Claude。注意兩個限制：用 Bash 改檔不會觸發；
  而且這只是「讓它看到失敗」，修改不會被撤銷，它也不一定修得好。

**動手做**
1. 輸入 `/hooks` 看目前的設定。
2. 製造回饋迴路：「把 `add()` 的 id 改成從 0 開始編號，只改 todo.py，不要改測試」
   → 改完後 hook 自動跑測試 → 失敗 → Claude 收到錯誤訊息。觀察它怎麼反應。
3. 測試護欄：「幫我用 rm -rf 刪掉 app 資料夾」→ 被 guard.py 擋下，Claude 會看到原因。
4. 「直接編輯 todos.json 把第 2 項改成已完成」→ 被擋，Claude 應該改用 CLI。

**練習**
- 加一個 `Stop` hook：Claude 每次回答完，在 macOS 發通知（`osascript -e 'display notification "Claude 完成了"'`）。
- 回到 Lesson 1 的 docstring 規則：寫一個 PostToolUse hook 檢查新函式有沒有 docstring。
  這就是把「建議」升級成「自動檢查」。
- **找漏洞**：guard.py 擋得住所有遞迴刪除和改 `todos.json` 的方式嗎？不用真的執行危險指令，
  在自己的終端機把模擬事件餵給 hook 就能測（exit 0 代表放行）：
  ```bash
  echo '{"tool_name":"Bash","tool_input":{"command":"rm --recursive app"}}' | python3 .claude/hooks/guard.py; echo "exit=$?"
  ```
  再想幾種會漏掉的寫法。反過來也試試誤擋：請 Claude 執行 `echo "不要用 rm -rf"`，明明無害，會發生什麼事？
  結論：hook 是一層護欄，不是完整的安全邊界，要搭配 permission、git 備份等其他層一起用。
- **驗收關卡**：PostToolUse 只能回饋，而且 Bash 改檔會漏掉。寫一個 `Stop` hook：Claude 要結束時跑一次測試，
  失敗就 exit 2 不讓它結束。這樣不管它用什麼方式改檔，測試沒過就交不了差。
  （提示：stdin 的 JSON 有 `stop_hook_active` 欄位，用它避免無限迴圈。）
- 想一想：權限（`permissions.allow`）和 PreToolUse hook 都能控制「能不能做」，差在哪？
  （提示：permission 是靜態規則；hook 是程式，可以看內容做判斷。）

---

## Lesson 5：Subagent —— 分工與隔離 context

**概念**：Subagent 在**獨立的 context** 裡工作，做完只把結論回傳主對話。
好處：主對話不會被大量的中間過程塞滿；可以給它不同的工具權限和角色。

**動手做**
1. 輸入 `/context`，在「Custom agents」區塊看到 `reviewer`（約 84 tokens——平常只載入 name + description）。
   新版已移除 `/agents` 精靈，subagent 就是 `.claude/agents/` 底下的 Markdown 檔，直接編輯或請 Claude 幫你建立即可。
2. 做完 Lesson 3 的 delete 指令後說：「用 reviewer subagent 審查一下 app/ 的程式」。
3. 比較：主對話裡只多了一段審查結論，而不是 reviewer 讀過的所有檔案內容。

---

## Lesson 6：畢業專題 —— 把 harness 練到不用你插手

### 1. 固定任務，事先訂好驗收條件

每一輪都用同一段需求，驗收條件**事先**寫好，不能只聽 Claude 說「完成了」：

> 幫 todo 加上優先順序和到期日：`add` 支援 `--priority high|medium|low`（預設 medium）和 `--due YYYY-MM-DD`；
> `list` 依優先順序排序；新增 `overdue` 指令，列出已過期且未完成的項目。

驗收條件（每一輪跑完由**你**檢查）：
- [ ] `python3 -m unittest discover -s app -v` 全部通過，新功能都有測試
- [ ] 上面四個行為實際用 CLI 操作都正確
- [ ] 符合 CLAUDE.md 的慣例

### 2. 實驗流程：每一輪都從同一個起點開始

用 git tag 標記起點、每一輪開一個分支。這樣 harness 的改良和每一輪的結果都會保留下來，
不會被 `git reset --hard` 一起洗掉。

```bash
# 0. 標記起點：目前的程式 + 原始 harness
git add -A && git commit -m "Lesson 6 起點"
git tag harness-v1

# 1. 第一輪：從起點開分支，開新的 claude，貼上任務
git switch -c run-v1-1 harness-v1
claude                                        # 盡量不插手，把問題記在筆記上
git add -A && git commit -m "v1 第 1 輪結果"     # 跑完把結果存起來

# 2. 改良 harness：回到起點開分支，依筆記只改 harness（CLAUDE.md、.claude/），不碰 app/
git switch -c harness-v2-edit harness-v1
git add -A && git commit -m "harness v2：<改了什麼>"
git tag harness-v2

# 3. 第二輪：從新起點開分支，貼上同一個任務
git switch -c run-v2-1 harness-v2
claude
git add -A && git commit -m "v2 第 1 輪結果"

# 4. 比較兩輪的程式差異
git diff run-v1-1 run-v2-1 -- app/
```

- **跑的過程中先不要改 harness**：一邊跑一邊改，就分不清變好是哪個改動造成的。
  真的卡住必須插手也沒關係，記下來就好——「人工介入次數」本身就是指標。
- **每一輪都重開 `claude`**：CLAUDE.md 等設定在對話開始時載入，新的對話也不會帶著上一輪的記憶。

### 3. 歸因：問題該補在哪一層？

| 它出了什麼問題 | 補在哪一層 |
|---|---|
| 不知道專案的某個慣例 | CLAUDE.md |
| 某類任務的步驟老是做錯或漏掉 | Skill |
| 某件事「絕對」不能漏或不能做 | Hook / Permission（記得驗證涵蓋範圍） |
| 需要它本來拿不到的資訊 | MCP |
| 主對話被塞爆、開始變笨 | Subagent、`/clear`、`/compact` |
| 改壞了卻不知道 | 補測試，並讓 hook 自動跑 |

不是每次失敗都要加規則。先判斷原因：是需求沒講清楚、測試不夠、工具做不到，還是流程真的要調整？
只補真正缺的那一層，harness 才不會越長越臃腫。

### 4. 記錄與比較

模型每次的表現都有變異，一次成功不代表 harness 真的變好。每個 harness 版本至少跑 2–3 輪
（`run-v1-2`、`run-v1-3`…都從同一個 tag 開分支），模型與 Claude Code 版本也要固定（`claude --version`、`/model`）。

| 指標 | harness v1 | harness v2 |
|---|---|---|
| 通過驗收次數 / 執行次數 | | |
| 人工介入次數 | | |
| 有沒有漏跑測試 | | |
| 有沒有違反 CLAUDE.md 慣例 | | |
| 花費時間 | | |

這個「觀察 → 歸因到哪一層 → 改 harness → 重跑比較」的迴圈，就是 Harness Engineering。
