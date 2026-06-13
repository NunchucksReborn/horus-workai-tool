# Manual Task Input

## Goal

Cho phep user nhap thu cong mo ta cong viec (thay vi quet log chat) de AI wrap thanh task theo cung Rule A-H + format chuan (>=50 char, `[Hanh dong] - [Muc tieu]`), giu nguyen flow TONG HOP hien tai.

## Context

User khong thuong xuyen chat cong viec (thoi quen trao doi truc tiep), nen flow quet log Rocket.Chat it y nghia. Tinh nang moi cung cap entry point de user tu mo ta cong viec cuoi ngay, AI wrap theo cung rule, render trong tab rieng.

## API

- `wrap_user_tasks(tasks, provider, api_key, user_name) -> str` (ai_processor.py moi)
  - Input: `tasks: List[{title, description, date}]` (date optional, default today)
  - Output: JSON string array `[{title, date}]` voi title da duoc wrap theo Rule B
  - Reuses: `get_system_rules()`, `call_ai_provider()`
- `POST /api/raw_tasks/from_text` (app_core.py moi)
  - Request: `{tasks: [{title, description, date}]}`
  - Response: `{status, tasks: [task objects da luu vao saved_raw_tasks.json]}`
  - Validation: 400 neu tasks rong/thieu, 500 neu AI fail

## Files

- `ai_processor.py` — them `wrap_user_tasks()` (~55 dong)
- `app_core.py` — them endpoint `from_text` (~40 dong)
- `static/index.html` — them nut `2. Nhap thu cong` + tab moi `tab-manual` (~50 dong)
- `static/app.js` — handler nut + add/remove row + submit + render Phan 2 (~160 dong)
- `static/style.css` — style cho form + phan tach AI (~80 dong)
- `tests/test_ai_processor.py` (moi) — unit test `wrap_user_tasks` (~80 dong)
- `tests/test_app_core_from_text.py` (moi) — test endpoint mock AI (~70 dong)

## UI Flow

```
Sidebar                          Tab "Nhap thu cong" (tab-manual)
+----------+         +---------------------------------+
| 1. Tong  |         |  PHAN 1: NHAP CUA USER          |
| 2. Nhap  |  click  |  +-- Task 1 ---- [X] ----+     |
|    thu   | ------> |  | Title*:  [______]      |     |
|    cong  |         |  | Mo ta:   [______]      |     |
| 3. Tao   |         |  | Date:    [2026-06-13]  |     |
| 4. Nhap  |         |  +------------------------+     |
| 5. Sua   |         |  +-- Task 2 ...            |     |
| Cai dat  |         |  +------------------------+     |
+----------+         |  [+ Them task]                 |
                     |  [AI tao task]                 |
                     |                                 |
                     |  ------ AI da wrap ------       |
                     |                                 |
                     |  PHAN 2: TASK AI SINH           |
                     |  +-- Task 1 -- Project:[v]--+   |
                     |  | AI Title (>=50 char)     |   |
                     |  | Date: 2026-06-13         |   |
                     |  | [Chi tiet] [Xoa]         |   |
                     |  +--------------------------+   |
                     +---------------------------------+
```

## Data Model

Task duoc luu vao `saved_raw_tasks.json` (cung file voi task sync), schema bo sung:

| Field       | Type | Default          | Muc dich                          |
|-------------|------|------------------|-----------------------------------|
| `id`        | str  | `task_{ms}_{i}`  | Tu sinh (giong task sync)         |
| `status`    | str  | `"active"`       | active / hide                     |
| `room_name` | str  | `"Thu cong"`     | Phan biet voi task tu chat        |
| `sender`    | str  | tu `config.json` | Ten hien thi user (giong task sync) |
| `text`      | str  | (AI wrap)        | Title da AI wrap theo Rule B      |
| `project_code` | str | `""`           | User gan sau (nhu Tab 1)          |
| `original_chat` | str | input goc      | Audit/backup input user           |
| `manual`    | bool | `true`           | Danh dau task tu form             |
| `form_date` | str  | today            | Date user nhap trong form         |

`tab-raw` (Tab 1) hien thi TAT CA tasks (gồm ca "Thu cong"), khong can thay doi.
`tab-manual` (tab moi) filter theo `room_name == "Thu cong"`.

## AI Prompt (wrap_user_tasks)

System prompt (~20 dong) yeu cau AI:
- Voi moi task input co title (+optional description):
  - Wrap title thanh format Rule B: `[Hanh dong cu the] - [Muc tieu cu the]`
  - Neu title < 50 char: dung `description` de bo sung hanh dong/muc tieu
  - Neu description rong: tu suy ra muc tieu tu title
  - Giu `date` user nhap
- Tra JSON array `[{title, date}]`

## Edge Cases

| Case                                   | Xu ly                                                         |
|----------------------------------------|---------------------------------------------------------------|
| Submit voi 0 task                      | Disable nut "AI tao task" khi list rong                       |
| Tat ca field Title rong                | Filter ra truoc khi gui AI                                    |
| Bam submit 2 lan lien tiep             | Disable nut, spinner                                          |
| AI fail / JSON loi                     | Fallback: dung `title` goc ghep `description`                 |
| AI tra JSON truncated                  | Dung `try_repair_json()` da co (`app_core.py:886`)            |
| User date trong tuong lai / qua khu xa | Khong validate (user tu quyet)                                |
| Render lai tab sau dong/mo             | Fetch lai tu `saved_raw_tasks.json` filter `room_name="Thu cong"` |
| Xoa task trong Phan 2                  | `hide` (giong Tab 1), khong xoa that                          |
| 3 nut trong sidebar doi so             | Doi so: 1.Tong hop, 2.Nhap thu cong, 3.Tao viec, 4.Nhap viec, 5.Sua KPI |

## Done when

- [ ] `wrap_user_tasks` co it nhat 6 unit test pass
- [ ] Endpoint `/api/raw_tasks/from_text` co it nhat 6 integration test pass
- [ ] Frontend: nut `2. Nhap thu cong` render, modal hien thi
- [ ] User nhap 1+ task -> AI wrap -> render Phan 2 - toan bo flow PASS
- [ ] Task moi co `room_name="Thu cong"`, xuat hien trong Tab 1 va tab-manual
- [ ] User co the gan project + xoa task trong Phan 2 (su dung API co san)
- [ ] Sidebar 5 nut duoc doi so dung (Tao viec 3, Nhap viec 4, Sua KPI 5)
- [ ] `git log --oneline` cho thay cac commit theo Phase 3 (RED -> GREEN)
- [ ] `python -m pytest` pass 100% (bao gom test cu)
