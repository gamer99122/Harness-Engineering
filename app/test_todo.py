import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import todo


class LogicTests(unittest.TestCase):
    def test_add_assigns_incrementing_ids(self):
        todos = []
        self.assertEqual(todo.add(todos, "a")["id"], 1)
        self.assertEqual(todo.add(todos, "b")["id"], 2)

    def test_add_after_gap_uses_max_id(self):
        todos = [{"id": 5, "title": "x", "done": False}]
        self.assertEqual(todo.add(todos, "y")["id"], 6)

    def test_mark_done(self):
        todos = [{"id": 1, "title": "a", "done": False}]
        todo.mark_done(todos, 1)
        self.assertTrue(todos[0]["done"])

    def test_mark_done_missing_id_raises(self):
        with self.assertRaises(KeyError):
            todo.mark_done([], 1)

    def test_format_todo(self):
        self.assertEqual(todo.format_todo({"id": 3, "title": "讀書", "done": True}), "[x] 3. 讀書")


class CliTests(unittest.TestCase):
    """透過 main() 跑完整流程，用 TODO_DB 指到暫存檔，不會動到真正的 todos.json。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = os.environ.get("TODO_DB")
        os.environ["TODO_DB"] = str(Path(self.tmp.name) / "todos.json")

    def tearDown(self):
        if self.old_db is None:
            os.environ.pop("TODO_DB", None)
        else:
            os.environ["TODO_DB"] = self.old_db
        self.tmp.cleanup()

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = todo.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_add_then_list(self):
        self.run_cli("add", "買牛奶")
        code, out, _ = self.run_cli("list")
        self.assertEqual(code, 0)
        self.assertIn("[ ] 1. 買牛奶", out)

    def test_done_unknown_id_returns_1(self):
        code, _, err = self.run_cli("done", "99")
        self.assertEqual(code, 1)
        self.assertIn("找不到", err)


if __name__ == "__main__":
    unittest.main()
