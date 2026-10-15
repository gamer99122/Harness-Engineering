# 範例：新增 `rename` 指令

> 這個檔案只有在 Claude 需要時才會被讀進 context（progressive disclosure）。
> SKILL.md 保持精簡，細節放在這裡。

## 1. 業務邏輯函式

```python
def rename(todos: list[dict], todo_id: int, title: str) -> dict:
    for t in todos:
        if t["id"] == todo_id:
            t["title"] = title
            return t
    raise KeyError(todo_id)
```

## 2. 接上 CLI

```python
p_rename = sub.add_parser("rename", help="修改待辦標題")
p_rename.add_argument("id", type=int)
p_rename.add_argument("title")
...
elif args.command == "rename":
    try:
        t = rename(todos, args.id, args.title)
    except KeyError:
        print(f"找不到 id={args.id} 的待辦", file=sys.stderr)
        return 1
    save(path, todos)
    print(f"已改名：{format_todo(t)}")
```

## 3. 測試

```python
def test_rename(self):
    todos = [{"id": 1, "title": "舊", "done": False}]
    todo.rename(todos, 1, "新")
    self.assertEqual(todos[0]["title"], "新")

def test_rename_missing_id_raises(self):
    with self.assertRaises(KeyError):
        todo.rename([], 1, "x")

# CliTests 裡：
def test_rename_cli(self):
    self.run_cli("add", "舊")
    code, out, _ = self.run_cli("rename", "1", "新")
    self.assertEqual(code, 0)
    self.assertIn("新", out)
```

## 4. 冒煙測試

```bash
python3 .claude/skills/add-command/scripts/smoke_test.py rename 1 新標題
```
