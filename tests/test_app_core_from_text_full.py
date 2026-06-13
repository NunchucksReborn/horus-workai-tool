"""Integration tests for POST /api/raw_tasks/from_text_full.

Tests use FastAPI TestClient + tmp_path to isolate file I/O.
AI is mocked via unittest.mock to avoid real API calls.
"""
import json
import os
import pytest
from unittest.mock import patch


def _make_client_and_dir(tmp_path, monkeypatch, config_data=None):
    """Helper: setup isolated BASE_DIR + test client using monkeypatch."""
    cfg = config_data or {
        "ai_provider": "openai",
        "ai_key": "test_key_123",
        "name": "Chu Van Mai",
        "rocket_username": "maicv",
    }
    (tmp_path / "config.json").write_text(json.dumps(cfg), encoding="utf-8")

    monkeypatch.setattr("app_core.BASE_DIR", str(tmp_path))
    monkeypatch.setattr("app_core.CONFIG_FILE", str(tmp_path / "config.json"))

    from app_core import app
    from fastapi.testclient import TestClient
    return TestClient(app), tmp_path


def test_from_text_full_missing_tasks_returns_400(tmp_path, monkeypatch):
    client, _ = _make_client_and_dir(tmp_path, monkeypatch)
    resp = client.post("/api/raw_tasks/from_text_full", json={})
    assert resp.status_code == 400


def test_from_text_full_empty_tasks_returns_400(tmp_path, monkeypatch):
    client, _ = _make_client_and_dir(tmp_path, monkeypatch)
    resp = client.post("/api/raw_tasks/from_text_full", json={"tasks": []})
    assert resp.status_code == 400


def test_from_text_full_valid_single_task_persists_full_fields(tmp_path, monkeypatch):
    """Task hợp lệ -> 200, file có text + description + acceptance_criteria."""
    client, base = _make_client_and_dir(tmp_path, monkeypatch)
    with patch("ai_processor.wrap_user_tasks_full") as mock_wrap:
        mock_wrap.return_value = json.dumps([
            {
                "title": "Hop team thong nhat scope - De phan cong ro rang cho sprint moi",
                "description": "1. Background: x\n2. Objective: y\n3. Notes: z",
                "acceptance_criteria": "1. AC1\n2. AC2",
                "date": "2026-06-13",
            }
        ], ensure_ascii=False)
        resp = client.post("/api/raw_tasks/from_text_full", json={
            "tasks": [
                {"title": "Hop team", "description": "thong nhat scope", "date": "2026-06-13", "project_code": "GRPG"}
            ]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["tasks"]) == 1
        task = data["tasks"][0]
        # Verify ALL fields present
        assert task["text"] == "Hop team thong nhat scope - De phan cong ro rang cho sprint moi"
        assert "1. Background" in task["description"]
        assert "AC1" in task["acceptance_criteria"]
        assert task["room_name"] == "Thu cong"
        assert task["manual"] is True
        assert task["form_date"] == "2026-06-13"
        assert task["project_code"] == "GRPG"
        # Verify file written
        saved = json.loads((base / "saved_raw_tasks.json").read_text(encoding="utf-8"))
        assert len(saved) == 1
        assert saved[0]["description"]  # not empty


def test_from_text_full_multiple_tasks_with_missing_description_still_works(tmp_path, monkeypatch):
    """2 task, 1 cai thieu description -> ca 2 van wrap OK."""
    client, base = _make_client_and_dir(tmp_path, monkeypatch)
    with patch("ai_processor.wrap_user_tasks_full") as mock_wrap:
        mock_wrap.return_value = json.dumps([
            {"title": "Task 1 wrap full - De hoan thanh cong viec trong ngay", "description": "1. Background\n2. Objective\n3. Notes", "acceptance_criteria": "1. AC1\n2. AC2", "date": "2026-06-13"},
            {"title": "Task 2 wrap full - De hoan thanh cong viec trong ngay", "description": "1. Background\n2. Objective\n3. Notes", "acceptance_criteria": "1. AC1\n2. AC2", "date": "2026-06-13"},
        ], ensure_ascii=False)
        resp = client.post("/api/raw_tasks/from_text_full", json={
            "tasks": [
                {"title": "Task 1", "description": "mo ta 1", "date": "2026-06-13", "project_code": "GRPG"},
                {"title": "Task 2", "description": "", "date": "2026-06-13", "project_code": "VCNDA"},  # description rong
            ]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["tasks"]) == 2


def test_from_text_full_all_empty_titles_returns_400(tmp_path, monkeypatch):
    """Tat ca title rong (sau strip) -> 400, khong luu task nao."""
    client, base = _make_client_and_dir(tmp_path, monkeypatch)
    resp = client.post("/api/raw_tasks/from_text_full", json={
        "tasks": [
            {"title": "", "description": "d1", "date": "2026-06-13"},
            {"title": "   ", "description": "d2", "date": "2026-06-13"},
        ]
    })
    assert resp.status_code == 400
    assert not (base / "saved_raw_tasks.json").exists()
