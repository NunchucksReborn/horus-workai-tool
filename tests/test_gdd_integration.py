"""Integration tests for GDD loading, caching, and from_text_full with project_code validation."""
import json
import os
import pytest
from unittest.mock import patch, MagicMock, mock_open


def _make_client_and_dir(tmp_path, monkeypatch, config_data=None, gdd_files=None):
    """Helper: setup isolated BASE_DIR + test client + optional GDD files."""
    cfg = config_data or {
        "ai_provider": "openai",
        "ai_key": "test_key_123",
        "name": "Chu Van Mai",
    }
    (tmp_path / "config.json").write_text(json.dumps(cfg), encoding="utf-8")

    if gdd_files:
        gdd_dir = tmp_path / "gdd"
        gdd_dir.mkdir(exist_ok=True)
        for code, content in gdd_files.items():
            (gdd_dir / f"{code}.md").write_text(content, encoding="utf-8")

    monkeypatch.setattr("app_core.BASE_DIR", str(tmp_path))
    monkeypatch.setattr("app_core.CONFIG_FILE", str(tmp_path / "config.json"))

    from app_core import app
    from fastapi.testclient import TestClient
    return TestClient(app), tmp_path


def test_get_gdd_loads_file_on_first_call(tmp_path, monkeypatch):
    """get_gdd load file lan dau, cache cho lan sau."""
    gdd_content = "# GRPG\nGame RPG noi dung test"
    client, base = _make_client_and_dir(tmp_path, monkeypatch, gdd_files={"GRPG": gdd_content})

    from app_core import get_gdd, gdd_cache
    gdd_cache.clear()

    result = get_gdd("GRPG")
    assert result == gdd_content
    assert gdd_cache["GRPG"] == gdd_content


def test_get_gdd_uses_cache_on_subsequent_calls(tmp_path, monkeypatch):
    """get_gdd khong doc file lan 2, tra cache."""
    gdd_content = "# GRPG cached"
    client, base = _make_client_and_dir(tmp_path, monkeypatch, gdd_files={"GRPG": gdd_content})

    from app_core import get_gdd, gdd_cache
    gdd_cache.clear()

    # Pre-fill cache (simulate da load truoc do)
    gdd_cache["GRPG"] = gdd_content

    # Neu file bi xoa nhung cache con -> van tra content
    (base / "gdd" / "GRPG.md").unlink()

    result = get_gdd("GRPG")
    assert result == gdd_content


def test_get_gdd_returns_none_for_missing_project(tmp_path, monkeypatch):
    """get_gdd tra None khi khong co file GDD."""
    client, base = _make_client_and_dir(tmp_path, monkeypatch, gdd_files={})

    from app_core import get_gdd, gdd_cache
    gdd_cache.clear()

    result = get_gdd("NONEXIST")
    assert result is None
    assert gdd_cache["NONEXIST"] is None


def test_from_text_full_validates_project_code_required(tmp_path, monkeypatch):
    """Task thieu project_code -> 400."""
    client, base = _make_client_and_dir(tmp_path, monkeypatch, gdd_files={"GRPG": "# GRPG"})

    with patch("ai_processor.wrap_user_tasks_full") as mock_wrap:
        resp = client.post("/api/raw_tasks/from_text_full", json={
            "tasks": [
                {"title": "Task 1", "description": "d1", "date": "2026-06-13", "project_code": "GRPG"},
                {"title": "Task 2", "description": "d2", "date": "2026-06-13", "project_code": ""},  # empty
            ]
        })
        assert resp.status_code == 400
        assert "project" in resp.json().get("detail", "").lower()
        # AI khong duoc goi neu validation fail
        assert not mock_wrap.called


def test_from_text_full_loads_gdd_and_passes_to_ai(tmp_path, monkeypatch):
    """Happy path: 2 task co project, GDD files ton tai -> AI nhan gdd_map."""
    gdd_files = {
        "GRPG": "# GRPG\nNoi dung RPG",
        "VCNDA": "# VCNDA\nNoi dung VCNDA",
    }
    client, base = _make_client_and_dir(tmp_path, monkeypatch, gdd_files=gdd_files)

    with patch("ai_processor.wrap_user_tasks_full") as mock_wrap:
        mock_wrap.return_value = json.dumps([
            {"title": "Task 1 wrap du 50 ky tu Rule B de test GDD integration - De test", "description": "1. BG\n2. Obj\n3. Notes", "acceptance_criteria": "1. AC1", "date": "2026-06-13"},
            {"title": "Task 2 wrap du 50 ky tu Rule B de test GDD integration - De test", "description": "1. BG\n2. Obj\n3. Notes", "acceptance_criteria": "1. AC1", "date": "2026-06-13"},
        ], ensure_ascii=False)

        resp = client.post("/api/raw_tasks/from_text_full", json={
            "tasks": [
                {"title": "Task 1", "description": "d1", "date": "2026-06-13", "project_code": "GRPG"},
                {"title": "Task 2", "description": "d2", "date": "2026-06-13", "project_code": "VCNDA"},
            ]
        })
        assert resp.status_code == 200
        # Verify wrap_user_tasks_full duoc goi voi gdd_map
        assert mock_wrap.called
        call_kwargs = mock_wrap.call_args.kwargs
        assert "gdd_map" in call_kwargs
        gdd_map = call_kwargs["gdd_map"]
        assert "GRPG" in gdd_map
        assert "VCNDA" in gdd_map
        assert "Noi dung RPG" in gdd_map["GRPG"]


def test_endpoint_get_gdd_returns_content(tmp_path, monkeypatch):
    """GET /api/projects/{code}/gdd tra 200 + content."""
    gdd_content = "# GRPG\nNoi dung GDD cho GRPG project"
    client, base = _make_client_and_dir(tmp_path, monkeypatch, gdd_files={"GRPG": gdd_content})

    from app_core import gdd_cache
    gdd_cache.clear()

    resp = client.get("/api/projects/GRPG/gdd")
    assert resp.status_code == 200
    assert "Noi dung GDD cho GRPG" in resp.text


def test_endpoint_get_gdd_404_for_missing(tmp_path, monkeypatch):
    """GET /api/projects/{code}/gdd tra 404 khi khong co file."""
    client, base = _make_client_and_dir(tmp_path, monkeypatch, gdd_files={})

    from app_core import gdd_cache
    gdd_cache.clear()

    resp = client.get("/api/projects/NONEXIST/gdd")
    assert resp.status_code == 404
