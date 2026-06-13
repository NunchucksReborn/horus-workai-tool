"""Unit tests for wrap_user_tasks_full with gdd_map support."""
import json
import pytest
from unittest.mock import patch


def test_wrap_full_includes_gdd_in_system_prompt():
    """Khi co gdd_map, system prompt phai chua noi dung GDD."""
    with patch("ai_processor.call_ai_provider") as mock_ai:
        mock_ai.return_value = json.dumps([
            {
                "title": "Task wrap du 50 ky tu theo Rule B de test GDD context integration - De test",
                "description": "1. Background\n2. Objective\n3. Notes",
                "acceptance_criteria": "1. AC1",
                "date": "2026-06-13",
            }
        ], ensure_ascii=False)

        from ai_processor import wrap_user_tasks_full

        gdd_map = {
            "GRPG": "# GRPG\n\nGame RPG theo turn-based, target 18-35 tuoi, mobile + PC."
        }
        wrap_user_tasks_full(
            [{"title": "Test", "description": "test", "date": "2026-06-13"}],
            "openai",
            "test_key",
            "Chu Van Mai",
            gdd_map=gdd_map,
        )

        # call_ai_provider(provider, api_key, system_prompt, user_prompt, ...)
        call_args = mock_ai.call_args
        system_prompt = call_args[0][2]
        assert "GRPG" in system_prompt
        assert "Game RPG theo turn-based" in system_prompt


def test_wrap_full_no_gdd_when_gdd_map_is_none():
    """Khi gdd_map=None (mac dinh), system prompt KHONG co section GDD (backward compat)."""
    with patch("ai_processor.call_ai_provider") as mock_ai:
        mock_ai.return_value = json.dumps([
            {
                "title": "Task wrap du 50 ky tu theo Rule B de test backward compat - De test",
                "description": "1. Background\n2. Objective\n3. Notes",
                "acceptance_criteria": "1. AC1",
                "date": "2026-06-13",
            }
        ], ensure_ascii=False)

        from ai_processor import wrap_user_tasks_full

        wrap_user_tasks_full(
            [{"title": "Test", "description": "test", "date": "2026-06-13"}],
            "openai",
            "test_key",
            "Chu Van Mai",
        )

        system_prompt = mock_ai.call_args[0][2]
        assert "BOI CANH DU AN" not in system_prompt
        assert "GDD" not in system_prompt


def test_wrap_full_no_gdd_when_gdd_map_is_empty_dict():
    """Khi gdd_map={} (empty), system prompt KHONG co section GDD."""
    with patch("ai_processor.call_ai_provider") as mock_ai:
        mock_ai.return_value = json.dumps([
            {
                "title": "Task wrap du 50 ky tu theo Rule B de test empty gdd map - De test",
                "description": "1. Background\n2. Objective\n3. Notes",
                "acceptance_criteria": "1. AC1",
                "date": "2026-06-13",
            }
        ], ensure_ascii=False)

        from ai_processor import wrap_user_tasks_full

        wrap_user_tasks_full(
            [{"title": "Test", "description": "test", "date": "2026-06-13"}],
            "openai",
            "test_key",
            "Chu Van Mai",
            gdd_map={},
        )

        system_prompt = mock_ai.call_args[0][2]
        assert "BOI CANH DU AN" not in system_prompt


def test_wrap_full_concatenates_multiple_gdd_entries():
    """Khi gdd_map co nhieu project, concat theo format '=== CODE ==='."""
    with patch("ai_processor.call_ai_provider") as mock_ai:
        mock_ai.return_value = json.dumps([
            {
                "title": "Task wrap du 50 ky tu theo Rule B de test multi GDD - De test",
                "description": "1. Background\n2. Objective\n3. Notes",
                "acceptance_criteria": "1. AC1",
                "date": "2026-06-13",
            }
        ], ensure_ascii=False)

        from ai_processor import wrap_user_tasks_full

        gdd_map = {
            "GRPG": "Noi dung GDD GRPG",
            "VCNDA": "Noi dung GDD VCNDA",
            "GCCF": "Noi dung GDD GCCF",
        }
        wrap_user_tasks_full(
            [{"title": "Test", "description": "test", "date": "2026-06-13"}],
            "openai",
            "test_key",
            "Chu Van Mai",
            gdd_map=gdd_map,
        )

        system_prompt = mock_ai.call_args[0][2]
        assert "=== GRPG ===" in system_prompt
        assert "=== VCNDA ===" in system_prompt
        assert "=== GCCF ===" in system_prompt
        assert "Noi dung GDD GRPG" in system_prompt
        assert "Noi dung GDD VCNDA" in system_prompt
        assert "Noi dung GDD GCCF" in system_prompt
