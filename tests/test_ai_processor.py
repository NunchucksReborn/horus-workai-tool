"""Unit tests for ai_processor.wrap_user_tasks.

Tests follow TDD: written BEFORE implementation, all should FAIL initially.
"""
import json
import pytest
from unittest.mock import patch


def test_wrap_short_title_with_description_expands_to_min_50_chars():
    """Title < 50 char + description co -> AI wrap phai >= 50 char."""
    with patch("ai_processor.call_ai_provider") as mock_ai:
        mock_ai.return_value = json.dumps([
            {
                "title": "Hop team thong nhat scope sprint moi - De phan cong ro rang cho tung thanh vien trong team",
                "date": "2026-06-13",
            }
        ])
        from ai_processor import wrap_user_tasks

        result = wrap_user_tasks(
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
        assert len(data[0]["title"]) >= 50


def test_wrap_long_title_keeps_content():
    """Title >= 50 char (khong can mo rong) -> output giu title (hoac giu nguyen)."""
    long_title = "Fix bug login tren production va cap nhat tai lieu huong dan su dung - De dam bao he thong on dinh"
    with patch("ai_processor.call_ai_provider") as mock_ai:
        mock_ai.return_value = json.dumps([
            {"title": long_title, "date": "2026-06-13"}
        ])
        from ai_processor import wrap_user_tasks

        result = wrap_user_tasks(
            [
                {
                    "title": long_title,
                    "description": "",
                    "date": "2026-06-13",
                }
            ],
            "openai",
            "test_key",
            "Chu Van Mai",
        )
        data = json.loads(result)
        assert len(data) == 1
        # Title giu noi dung chinh (co the wrap nhe)
        assert "Fix bug login" in data[0]["title"] or "bug login" in data[0]["title"].lower()


def test_wrap_multiple_tasks_returns_all_in_order():
    """3 tasks input -> 3 outputs, dung thu tu."""
    wrapped_tasks = [
        {"title": "Task A da wrap thanh cong - De hoan thanh cong viec A trong ngay hom nay", "date": "2026-06-13"},
        {"title": "Task B da wrap thanh cong - De hoan thanh cong viec B trong ngay hom nay", "date": "2026-06-13"},
        {"title": "Task C da wrap thanh cong - De hoan thanh cong viec C trong ngay hom nay", "date": "2026-06-13"},
    ]
    with patch("ai_processor.call_ai_provider") as mock_ai:
        mock_ai.return_value = json.dumps(wrapped_tasks)
        from ai_processor import wrap_user_tasks

        result = wrap_user_tasks(
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


def test_wrap_preserves_user_date():
    """Date user nhap -> output giu nguyen date."""
    with patch("ai_processor.call_ai_provider") as mock_ai:
        mock_ai.return_value = json.dumps([
            {"title": "Task ngay 10 - De hoan thanh cong viec ngay 10 thang 6 theo yeu cau", "date": "2026-06-10"}
        ])
        from ai_processor import wrap_user_tasks

        result = wrap_user_tasks(
            [
                {
                    "title": "Task ngay 10",
                    "description": "lam gi do",
                    "date": "2026-06-10",
                }
            ],
            "openai",
            "test_key",
            "Chu Van Mai",
        )
        data = json.loads(result)
        assert data[0]["date"] == "2026-06-10"


def test_wrap_falls_back_to_original_title_when_ai_fails():
    """AI fail (raise exception) -> fallback dung title goc + description."""
    with patch("ai_processor.call_ai_provider") as mock_ai:
        mock_ai.side_effect = Exception("API down")
        from ai_processor import wrap_user_tasks

        result = wrap_user_tasks(
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
        # Fallback: ghep title + description
        assert "Fix bug" in data[0]["title"]
        assert "sua loi login" in data[0]["title"]
        assert data[0]["date"] == "2026-06-13"


def test_wrap_returns_valid_json_for_multiple_tasks():
    """Nhieu task -> output la JSON string parseable, khong co text thua."""
    with patch("ai_processor.call_ai_provider") as mock_ai:
        mock_ai.return_value = "```json\n[{\"title\": \"Task 1 wrapped\", \"date\": \"2026-06-13\"}, {\"title\": \"Task 2 wrapped\", \"date\": \"2026-06-13\"}]\n```"
        from ai_processor import wrap_user_tasks

        result = wrap_user_tasks(
            [
                {"title": "T1", "description": "d1", "date": "2026-06-13"},
                {"title": "T2", "description": "d2", "date": "2026-06-13"},
            ],
            "openai",
            "test_key",
            "Chu Van Mai",
        )
        # Phai parse duoc JSON (loai bo markdown fence)
        data = json.loads(result)
        assert len(data) == 2
        assert all("title" in t and "date" in t for t in data)
