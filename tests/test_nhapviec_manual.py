"""Integration tests for POST /api/run/nhapviec_manual.

Tests use FastAPI TestClient + tmp_path. Submitter spawn is mocked.
"""
import json
import os
import pytest
from unittest.mock import patch, MagicMock


def _make_client_and_dir(tmp_path, monkeypatch, manual_tasks=None, config_data=None):
    """Helper: setup isolated BASE_DIR + pre-seed saved_raw_tasks.json with manual tasks."""
    cfg = config_data or {
        "ai_provider": "openai",
        "ai_key": "test_key_123",
        "name": "Chu Van Mai",
    }
    (tmp_path / "config.json").write_text(json.dumps(cfg), encoding="utf-8")

    if manual_tasks:
        (tmp_path / "saved_raw_tasks.json").write_text(json.dumps(manual_tasks), encoding="utf-8")

    monkeypatch.setattr("app_core.BASE_DIR", str(tmp_path))
    monkeypatch.setattr("app_core.CONFIG_FILE", str(tmp_path / "config.json"))

    from app_core import app
    from fastapi.testclient import TestClient
    return TestClient(app), tmp_path


def test_nhapviec_manual_no_manual_tasks_returns_400(tmp_path, monkeypatch):
    """Khong co manual task (room_name='Thu cong', status='active') -> 400."""
    client, _ = _make_client_and_dir(tmp_path, monkeypatch, manual_tasks=[
        {"id": "task_1", "room_name": "Other room", "status": "active", "project_code": "GRPG", "text": "Other", "form_date": "2026-06-13"}
    ])
    resp = client.post("/api/run/nhapviec_manual")
    assert resp.status_code == 400


def test_nhapviec_manual_missing_project_returns_400(tmp_path, monkeypatch):
    """Co task thieu project_code -> 400 voi message ro."""
    client, _ = _make_client_and_dir(tmp_path, monkeypatch, manual_tasks=[
        {"id": "task_1", "room_name": "Thu cong", "status": "active", "project_code": "", "text": "Task 1", "form_date": "2026-06-13", "description": "d1", "acceptance_criteria": "a1"},
        {"id": "task_2", "room_name": "Thu cong", "status": "active", "project_code": "GRPG", "text": "Task 2", "form_date": "2026-06-13", "description": "d2", "acceptance_criteria": "a2"},
    ])
    resp = client.post("/api/run/nhapviec_manual")
    assert resp.status_code == 400
    detail = resp.json().get("detail", "")
    assert "project" in detail.lower() or "chua gan" in detail.lower()


def test_nhapviec_manual_happy_path_writes_files_and_returns_200(tmp_path, monkeypatch):
    """2 task hop le -> 200, ghi memorytask_manual.md + tasks.json."""
    # Mock subprocess.Popen de tranh chay submitter that
    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = ("", "")
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        client, base = _make_client_and_dir(tmp_path, monkeypatch, manual_tasks=[
            {"id": "task_1", "room_name": "Thu cong", "status": "active", "project_code": "GRPG", "text": "Task 1 title", "form_date": "2026-06-13", "description": "1. Background\n2. Objective\n3. Notes", "acceptance_criteria": "1. AC1\n2. AC2"},
            {"id": "task_2", "room_name": "Thu cong", "status": "active", "project_code": "VCNDA", "text": "Task 2 title", "form_date": "2026-06-13", "description": "1. Background2", "acceptance_criteria": "1. AC1"},
        ])
        resp = client.post("/api/run/nhapviec_manual")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["task_count"] == 2

        # Verify memorytask_manual.md
        md_file = base / "memorytask_manual.md"
        assert md_file.exists()
        md_content = md_file.read_text(encoding="utf-8")
        assert "# Daily Tasks Manual" in md_content
        assert "Task 1 title" in md_content
        assert "GRPG" in md_content
        assert "VCNDA" in md_content
        assert "1. Background" in md_content
        assert "AC1" in md_content

        # Verify tasks.json
        json_file = base / "tasks.json"
        assert json_file.exists()


def test_nhapviec_manual_tasks_json_has_submitter_format(tmp_path, monkeypatch):
    """tasks.json phai co dung format submitter doc: title, project, date, status, sprint, description."""
    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = ("", "")
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        client, base = _make_client_and_dir(tmp_path, monkeypatch, manual_tasks=[
            {"id": "task_1", "room_name": "Thu cong", "status": "active", "project_code": "GRPG", "text": "Task 1 title", "form_date": "2026-06-13", "description": "1. Background\n2. Objective\n3. Notes", "acceptance_criteria": "1. AC1"},
        ])
        resp = client.post("/api/run/nhapviec_manual")
        assert resp.status_code == 200

        tasks_data = json.loads((base / "tasks.json").read_text(encoding="utf-8"))
        assert len(tasks_data) == 1
        t = tasks_data[0]
        assert t["title"] == "Task 1 title"
        assert t["project"] == "GRPG"
        assert t["date"] == "2026-06-13"
        assert t["status"] == "Done"
        assert t["sprint"] == "latest"
        # description phai chua "4. Acceptance Criteria:"
        assert "1. Background" in t["description"]
        assert "4. Acceptance Criteria:" in t["description"]
        assert "AC1" in t["description"]


def test_nhapviec_manual_memorytask_md_has_clean_markdown(tmp_path, monkeypatch):
    """memorytask_manual.md co Markdown dep voi Description + AC sections."""
    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = ("", "")
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        client, base = _make_client_and_dir(tmp_path, monkeypatch, manual_tasks=[
            {"id": "task_1", "room_name": "Thu cong", "status": "active", "project_code": "GRPG", "text": "Task 1 title", "form_date": "2026-06-13", "description": "1. Background: bg\n2. Objective: obj\n3. Notes: notes", "acceptance_criteria": "1. AC1\n2. AC2"},
        ])
        resp = client.post("/api/run/nhapviec_manual")
        assert resp.status_code == 200

        md_content = (base / "memorytask_manual.md").read_text(encoding="utf-8")
        # Co header + Task sections
        assert "# Daily Tasks Manual" in md_content
        assert "## Task 1" in md_content
        # Co project, date, title
        assert "**Project**: GRPG" in md_content
        assert "**Date**: 2026-06-13" in md_content
        assert "**Title**: Task 1 title" in md_content
        # Co Description + AC sections
        assert "**Description**" in md_content
        assert "**Acceptance Criteria**" in md_content
        assert "1. Background: bg" in md_content
        assert "1. AC1" in md_content
