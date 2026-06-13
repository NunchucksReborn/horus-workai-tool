"""Integration tests for POST /api/raw_tasks/from_text.

Tests use FastAPI TestClient + tmp_path to isolate file I/O.
AI is mocked via unittest.mock to avoid real API calls.
"""
import json
import os
import pytest
from unittest.mock import patch


def _make_client_and_dir(tmp_path, monkeypatch, config_data=None):
    """Helper: setup isolated BASE_DIR + test client using monkeypatch (persists for test)."""
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


def test_from_text_missing_tasks_returns_400(tmp_path, monkeypatch):
    client, _ = _make_client_and_dir(tmp_path, monkeypatch)
    resp = client.post("/api/raw_tasks/from_text", json={})
    assert resp.status_code == 400
    assert "tasks" in resp.json().get("detail", "").lower() or "thieu" in resp.json().get("detail", "").lower()


def test_from_text_all_empty_titles_returns_400(tmp_path, monkeypatch):
    """Tat ca title deu rong (sau strip) -> 400, khong luu task nao."""
    client, base = _make_client_and_dir(tmp_path, monkeypatch)
    resp = client.post("/api/raw_tasks/from_text", json={
        "tasks": [
            {"title": "", "description": "d1", "date": "2026-06-13"},
            {"title": "   ", "description": "d2", "date": "2026-06-13"},  # whitespace only
        ]
    })
    assert resp.status_code == 400
    # Verify khong co file nao duoc tao
    saved_file = base / "saved_raw_tasks.json"
    assert not saved_file.exists()


def test_from_text_empty_tasks_returns_400(tmp_path, monkeypatch):
    client, _ = _make_client_and_dir(tmp_path, monkeypatch)
    resp = client.post("/api/raw_tasks/from_text", json={"tasks": []})
    assert resp.status_code == 400


def test_from_text_valid_single_task_creates_file_and_returns_200(tmp_path, monkeypatch):
    client, base = _make_client_and_dir(tmp_path, monkeypatch)
    with patch("ai_processor.wrap_user_tasks") as mock_wrap:
        mock_wrap.return_value = json.dumps([
            {"title": "Hop team thong nhat scope - De cac thanh vien cung hieu huong di", "date": "2026-06-13"}
        ], ensure_ascii=False)
        resp = client.post("/api/raw_tasks/from_text", json={
            "tasks": [
                {"title": "Hop team", "description": "thong nhat scope", "date": "2026-06-13"}
            ]
        })
        if resp.status_code != 200:
            import sys
            print(f"DEBUG resp: {resp.status_code} body={resp.text}", file=sys.stderr)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert len(data["tasks"]) == 1
        # Verify file was written
        saved_file = base / "saved_raw_tasks.json"
        assert saved_file.exists()
        saved = json.loads(saved_file.read_text(encoding="utf-8"))
        assert len(saved) == 1


def test_from_text_multiple_tasks_with_missing_description_still_works(tmp_path, monkeypatch):
    client, base = _make_client_and_dir(tmp_path, monkeypatch)
    with patch("ai_processor.wrap_user_tasks") as mock_wrap:
        mock_wrap.return_value = json.dumps([
            {"title": "Task 1 da wrap thanh cong - De hoan thanh cong viec theo yeu cau PM", "date": "2026-06-13"},
            {"title": "Task 2 da wrap thanh cong - De hoan thanh cong viec theo yeu cau PM", "date": "2026-06-13"},
        ], ensure_ascii=False)
        resp = client.post("/api/raw_tasks/from_text", json={
            "tasks": [
                {"title": "Task 1", "description": "mo ta 1", "date": "2026-06-13"},
                {"title": "Task 2", "description": "", "date": "2026-06-13"},  # description rong
            ]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["tasks"]) == 2


def test_from_text_missing_api_key_returns_500_with_clear_message(tmp_path, monkeypatch):
    cfg = {
        "ai_provider": "openai",
        "ai_key": "",  # EMPTY
        "name": "Chu Van Mai",
    }
    client, _ = _make_client_and_dir(tmp_path, monkeypatch, config_data=cfg)
    resp = client.post("/api/raw_tasks/from_text", json={
        "tasks": [{"title": "Test", "description": "", "date": "2026-06-13"}]
    })
    assert resp.status_code == 500
    detail = resp.json().get("detail", "").lower()
    assert "ai" in detail or "key" in detail or "provider" in detail or "api" in detail


def test_from_text_persisted_task_has_correct_schema(tmp_path, monkeypatch):
    """Task luu vao file phai co room_name='Thu cong', manual=True."""
    client, base = _make_client_and_dir(tmp_path, monkeypatch)
    with patch("ai_processor.wrap_user_tasks") as mock_wrap:
        mock_wrap.return_value = json.dumps([
            {"title": "Wrap thanh cong - De theo doi tien do cong viec hang ngay cua PM", "date": "2026-06-13"}
        ], ensure_ascii=False)
        client.post("/api/raw_tasks/from_text", json={
            "tasks": [
                {"title": "Wrap thanh cong", "description": "theo doi tien do", "date": "2026-06-13"}
            ]
        })
        saved = json.loads((base / "saved_raw_tasks.json").read_text(encoding="utf-8"))
        assert len(saved) == 1
        task = saved[0]
        assert task["room_name"] == "Thu cong"
        assert task["manual"] is True
        assert task["status"] == "active"
        assert task["sender"] == "Chu Van Mai"
        assert task["form_date"] == "2026-06-13"
        assert "title" in task or "text" in task  # AI wrap title luu o 'text'
