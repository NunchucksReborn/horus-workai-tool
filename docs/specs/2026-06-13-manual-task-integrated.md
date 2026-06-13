# Manual Task Integrated (Tạo + Nhập trong tab-manual)

## Goal

Tich hop buoc Tao viec + Nhap viec vao trong tab-manual: user nhap form → bam "AI tao Task" → AI sinh Title + Description + AC → render Phan 2 → chon project → bam "Nhap viec ngay" → submitter chay luon. Flow cu (Tab 2/3) van giu nguyen song song.

## API

### New in `ai_processor.py`
- `wrap_user_tasks_full(tasks, provider, api_key, user_name) -> str`
  - Input: `tasks: List[{title, description, date}]`
  - Output: JSON string array `[{title, description, acceptance_criteria, date}]`
  - description = "1. Background: ...\n2. Objective: ...\n3. Notes: ..."
  - acceptance_criteria = "1. AC 1\n2. AC 2\n..."
  - Reuses: `get_system_rules()`, `call_ai_provider()`

### New in `app_core.py`
- `POST /api/raw_tasks/from_text_full`
  - Request: `{tasks: [{title, description, date}]}`
  - Validation: 400 if tasks missing/empty/all-empty-title
  - Calls `wrap_user_tasks_full`, persists to `saved_raw_tasks.json`
  - Returns `{status, tasks: [full task objects]}`
  - Task schema: `{id, status, room_name="Thu cong", sender, text=title, description, acceptance_criteria, project_code="", original_chat, manual=True, form_date}`

- `POST /api/run/nhapviec_manual`
  - No body
  - Validates: 400 if no manual tasks (room_name="Thu cong", status="active"), 400 if any task missing project_code
  - Writes `memorytask_manual.md` (markdown audit file with Description + AC)
  - Builds `tasks.json` with `{title, project, date, status="Done", sprint="latest", description, form_date}` for submitter
  - Spawns `submitter.py` as background subprocess
  - Returns `{status, message, task_count}`

## Files

| File | Thay doi | Dong uoc |
|---|---|---|
| `ai_processor.py` | them `wrap_user_tasks_full()` | +85 |
| `app_core.py` | them endpoint `from_text_full` + `nhapviec_manual` | +90 |
| `submitter.py` | skip click "Goi y bang AI" khi desc co san | +5 |
| `static/index.html` | nut "Nhap viec ngay" + modal Chi tiet skeleton | +25 |
| `static/app.js` | handler AI tao + render modal + poll status | +150 |
| `static/style.css` | style modal popup | +50 |
| `tests/test_ai_processor_full.py` (moi) | 6 unit test | +90 |
| `tests/test_nhapviec_manual.py` (moi) | 5 integration test | +80 |

## UI Flow

```
Sidebar                          Tab "Nhap thu cong" (tab-manual)
+----------+         +----------------------------------------+
| 1. Tong  |         |  PHAN 1: NHAP CUA USER                  |
| 2. Nhap  |  click  |  +-- Task 1 ---- [X] --+                |
|    thu   | ------> |  | Title:  [______]    |                |
|    cong  |         |  | Mo ta:  [______]    |                |
| 3. Tao   |         |  | Date:   [______]    |                |
| 4. Nhap  |         |  +---------------------+                |
| 5. Sua   |         |  [+ Them task]                            |
| Cai dat  |         |  [AI tao Task]                           |
+----------+         |                                          |
                     |  --- AI da wrap (Title + Desc + AC) ---  |
                     |                                          |
                     |  PHAN 2: TASK AI SINH                    |
                     |  +-- AI Task 1 ---------------------+    |
                     |  | Project: [Chon du an v]          |    |
                     |  | Title:  "Title da wrap..."       |    |
                     |  | Date: 2026-06-13                 |    |
                     |  | [Chi tiet] [Xoa]                 |    |
                     |  +---------------------------------+    |
                     |                                          |
                     |  [Nhap viec ngay] (khi co >= 1 task)     |
                     +----------------------------------------+

Khi bam "Chi tiet" → modal popup:
+----------------------------------+
|  Chi tiet Task             [X]  |
+----------------------------------+
|  Description                    |
|  1. Background: ...             |
|  2. Objective: ...              |
|  3. Notes: ...                  |
|                                  |
|  Acceptance Criteria            |
|  1. AC 1                        |
|  2. AC 2                        |
+----------------------------------+
```

## Data Model

### Task in `saved_raw_tasks.json` (after from_text_full)
```json
{
  "id": "task_{ms}_{i}",
  "status": "active",
  "room_name": "Thu cong",
  "sender": "Chu Van Mai",
  "text": "Title da wrap theo Rule B (>=50 char)",
  "description": "1. Background: <text>\n2. Objective: <text>\n3. Notes: <text>",
  "acceptance_criteria": "1. AC 1\n2. AC 2",
  "form_date": "2026-06-13",
  "project_code": "GRPG",
  "original_chat": "input goc cua user",
  "manual": true
}
```

### `memorytask_manual.md` (audit only)
```markdown
# Daily Tasks Manual — 2026-06-13

## Task 1
- **Project**: GRPG
- **Date**: 2026-06-13
- **Title**: [title da wrap]
- **Description**:
  1. Background: ...
  2. Objective: ...
  3. Notes: ...
- **Acceptance Criteria**:
  1. AC 1
  2. AC 2
```

### `tasks.json` (submitter input)
```json
[{
  "title": "...",
  "project": "GRPG",
  "date": "2026-06-13",
  "status": "Done",
  "sprint": "latest",
  "description": "1. Background...\n2. Objective...\n3. Notes...\n4. Acceptance Criteria: 1. AC 1\n2. AC 2"
}]
```

## AI Prompt (wrap_user_tasks_full)

System prompt yeu cau AI:
- Voi moi task input co title (+optional description):
  - Wrap title theo Rule B ([Hanh dong] - [Muc tieu], >=50 char)
  - Sinh description gom 3 phan: Background, Objective, Notes
  - Sinh acceptance_criteria: 2-5 tieu chi cu the, do luong duoc
  - Giu date user nhap
- Tra JSON array `[{title, description, acceptance_criteria, date}]`

## Edge Cases

| Case | Xu ly |
|---|---|
| AI fail wrap full | fallback: title goc + description/AC rong |
| Nhap viec khi thieu project | 400 "Vui long gan project cho tat ca task" |
| Submitter chay roi (tu Tab 3) | parallel OK, UI hien 2 status rieng |
| Modal Chi tiet | click overlay ben ngoai hoac X de dong |
| memorytask_manual.md ghi de | OK (chi audit, submitter doc tasks.json) |
| Task chua co Description (fallback case) | submitter se click AI goi y nhu cu |

## Done when

- [ ] `wrap_user_tasks_full` co 6 unit test pass
- [ ] Endpoint `from_text_full` co 5 integration test pass
- [ ] Endpoint `nhapviec_manual` co 5 integration test pass
- [ ] Submitter skip AI goi y khi description co san
- [ ] Frontend: nut "AI tao Task" + "Nhap viec ngay" + modal Chi tiet
- [ ] User flow end-to-end PASS: nhap form → AI wrap → modal hien Description+AC → gán project → nhap viec
- [ ] All old tests still pass
- [ ] Version bump 1.0.30
