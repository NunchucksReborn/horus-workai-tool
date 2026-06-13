"""Unit tests for ai_processor.wrap_user_tasks_full.

Tests follow TDD: written BEFORE implementation, all should FAIL initially.
"""
import json
import pytest
from unittest.mock import patch


def test_wrap_full_short_title_expands_title_and_includes_all_fields():
    """Input 1 task title ngan -> output full {title>=50, desc 3 phan, AC >=2, date}."""
    with patch("ai_processor.call_ai_provider") as mock_ai:
        mock_ai.return_value = json.dumps([
            {
                "title": "Hop team thong nhat scope sprint moi - De cac thanh vien cung hieu huong di va phan cong cong viec",
                "description": "1. Background: Can thong nhat scope cho sprint moi\n2. Objective: Dat duoc thoa thuan giua cac thanh vien\n3. Notes: Nen chuan bi truoc agenda",
                "acceptance_criteria": "1. Moi thanh vien hieu scope\n2. Co phan cong ro rang",
                "date": "2026-06-13",
            }
        ], ensure_ascii=False)
        from ai_processor import wrap_user_tasks_full

        result = wrap_user_tasks_full(
            [
                {
                    "title": "Hop team",
                    "description": "thong nhat scope sprint moi",
                    "date": "2026-06-13",
                }
            ],
            "openai",
            "test_key",
            "Chu Van Mai",
        )
        data = json.loads(result)
        assert len(data) == 1
        task = data[0]
        assert len(task["title"]) >= 50
        assert "description" in task
        assert "acceptance_criteria" in task
        assert task["date"] == "2026-06-13"


def test_wrap_full_returns_three_tasks_in_input_order():
    """Input 3 task -> output 3 objects dung thu tu."""
    wrapped = [
        {"title": "Task A da wrap thanh cong voi do dai du 50 ky tu - De hoan thanh A trong hom nay", "description": "1. Background: A\n2. Objective: A\n3. Notes: A", "acceptance_criteria": "1. AC1\n2. AC2", "date": "2026-06-13"},
        {"title": "Task B da wrap thanh cong voi do dai du 50 ky tu - De hoan thanh B trong hom nay", "description": "1. Background: B\n2. Objective: B\n3. Notes: B", "acceptance_criteria": "1. AC1\n2. AC2", "date": "2026-06-13"},
        {"title": "Task C da wrap thanh cong voi do dai du 50 ky tu - De hoan thanh C trong hom nay", "description": "1. Background: C\n2. Objective: C\n3. Notes: C", "acceptance_criteria": "1. AC1\n2. AC2", "date": "2026-06-13"},
    ]
    with patch("ai_processor.call_ai_provider") as mock_ai:
        mock_ai.return_value = json.dumps(wrapped, ensure_ascii=False)
        from ai_processor import wrap_user_tasks_full

        result = wrap_user_tasks_full(
            [
                {"title": "Task A", "description": "lam A", "date": "2026-06-13"},
                {"title": "Task B", "description": "lam B", "date": "2026-06-13"},
                {"title": "Task C", "description": "lam C", "date": "2026-06-13"},
            ],
            "openai",
            "test_key",
            "Chu Van Mai",
        )
        data = json.loads(result)
        assert len(data) == 3
        assert "A" in data[0]["title"]
        assert "B" in data[1]["title"]
        assert "C" in data[2]["title"]


def test_wrap_full_falls_back_to_empty_desc_ac_when_ai_fails():
    """AI fail -> fallback: title goc + description/AC rong (submitter se click AI goi y)."""
    with patch("ai_processor.call_ai_provider") as mock_ai:
        mock_ai.side_effect = Exception("API down")
        from ai_processor import wrap_user_tasks_full

        result = wrap_user_tasks_full(
            [
                {
                    "title": "Fix bug",
                    "description": "sua loi login",
                    "date": "2026-06-13",
                }
            ],
            "openai",
            "test_key",
            "Chu Van Mai",
        )
        data = json.loads(result)
        assert len(data) == 1
        # Fallback: title ghep voi description, description/AC rong
        assert "Fix bug" in data[0]["title"]
        assert data[0]["description"] == ""
        assert data[0]["acceptance_criteria"] == ""
        assert data[0]["date"] == "2026-06-13"


def test_wrap_full_description_contains_three_sections():
    """Output description phai co '1. Background', '2. Objective', '3. Notes'."""
    with patch("ai_processor.call_ai_provider") as mock_ai:
        mock_ai.return_value = json.dumps([
            {
                "title": "Test task title du 50 ky tu de pass Rule B de dang theo cong thuc - De test",
                "description": "1. Background: bg here\n2. Objective: obj here\n3. Notes: notes here",
                "acceptance_criteria": "1. AC 1\n2. AC 2",
                "date": "2026-06-13",
            }
        ], ensure_ascii=False)
        from ai_processor import wrap_user_tasks_full

        result = wrap_user_tasks_full(
            [{"title": "Test", "description": "test", "date": "2026-06-13"}],
            "openai",
            "test_key",
            "Chu Van Mai",
        )
        data = json.loads(result)
        desc = data[0]["description"]
        assert "1. Background" in desc
        assert "2. Objective" in desc
        assert "3. Notes" in desc


def test_wrap_full_acceptance_criteria_has_multiple_lines():
    """Output acceptance_criteria phai co >= 2 dong (moi dong bat dau bang so)."""
    with patch("ai_processor.call_ai_provider") as mock_ai:
        mock_ai.return_value = json.dumps([
            {
                "title": "Test title wrap du 50 ky tu theo Rule B de test acceptance criteria output - De test AC",
                "description": "1. Background: x\n2. Objective: y\n3. Notes: z",
                "acceptance_criteria": "1. AC 1 - kiem tra input\n2. AC 2 - kiem tra output\n3. AC 3 - kiem tra error",
                "date": "2026-06-13",
            }
        ], ensure_ascii=False)
        from ai_processor import wrap_user_tasks_full

        result = wrap_user_tasks_full(
            [{"title": "Test", "description": "test", "date": "2026-06-13"}],
            "openai",
            "test_key",
            "Chu Van Mai",
        )
        data = json.loads(result)
        ac = data[0]["acceptance_criteria"]
        lines = [l for l in ac.split("\n") if l.strip()]
        assert len(lines) >= 2


def test_wrap_full_preserves_user_date():
    """Date user nhap -> output giu nguyen date."""
    with patch("ai_processor.call_ai_provider") as mock_ai:
        mock_ai.return_value = json.dumps([
            {
                "title": "Task ngay 10 wrap thanh cong voi do dai du 50 ky tu - De hoan thanh ngay 10",
                "description": "1. Background: x\n2. Objective: y\n3. Notes: z",
                "acceptance_criteria": "1. AC",
                "date": "2026-06-10",
            }
        ], ensure_ascii=False)
        from ai_processor import wrap_user_tasks_full

        result = wrap_user_tasks_full(
            [{"title": "Task ngay 10", "description": "lam gi do", "date": "2026-06-10"}],
            "openai",
            "test_key",
            "Chu Van Mai",
        )
        data = json.loads(result)
        assert data[0]["date"] == "2026-06-10"
