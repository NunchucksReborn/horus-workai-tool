# GDD Context cho Tab Manual

## Goal

Cho phep user nap 1 file GDD (Game Design Document / project overview) cho moi project. Khi wrap user tasks trong tab-manual, AI su dung GDD lam context de sinh Description + Acceptance Criteria sat voi du an, thay vi "doan mo" chung chung.

## Context

Hien tai AI sinh Description + AC chi dua tren Title + description input cua user. WorkAI co project description nhung AI cua Athena khong biet. Ket qua: Des/AC "mong lung", khong sat voi domain cua project (game RPG, sandbox, training...).

## Approach

Moi project co 1 file `gdd/<project_code>.md` chua:
- Tong quan du an (genre, target audience, scope)
- Tinh nang chinh
- Tieu chi chat luong / quality bar
- Glossary (thuat ngu rieng cua project)

Khi user bam "AI tao Task" trong tab-manual:
1. Frontend gui tasks kem `project_code` (moi task phai co project - bat buoc)
2. Server group tasks theo `project_code` unique
3. Load GDD cho moi project (cache in-memory)
4. Inject GDD content vao system prompt cua AI
5. AI sinh Des/AC co context giong project that

## API changes

### Modified: `wrap_user_tasks_full(tasks, provider, api_key, user_name, gdd_map=None)`
- Them param `gdd_map: dict` (optional, `{project_code: gdd_content}`)
- Khi co gdd_map, inject vao system prompt voi format:
  ```
  BOI CANH DU AN (GDD):
  === GRPG ===
  <content gdd/GRPG.md>
  === VCNDA ===
  <content gdd/VCNDA.md>
  ```
- Backward compatible: neu gdd_map=None hoac empty, giu nguyen behavior cu

### Modified: `POST /api/raw_tasks/from_text_full`
- Input schema: moi task phai co `project_code` (mandatory)
- Validation: neu bat ky task nao thieu project_code -> 400 "Vui long gan project cho tat ca task truoc khi tao AI"
- Server load GDD theo project_code unique tu tasks, truyen vao `wrap_user_tasks_full`

### New: `GET /api/projects/{code}/gdd`
- Tra ve GDD content (text/markdown)
- 404 neu khong co file
- Dung cho UI debug (hien thi GDD cho user xem)

## Files

| File | Thay doi | Dong |
|---|---|---|
| `ai_processor.py` | `wrap_user_tasks_full` them gdd_map param | +30 |
| `app_core.py` | `gdd_cache` dict, `get_gdd()`, update from_text_full, them endpoint GET gdd | +50 |
| `static/app.js` | Form row them combobox project, validate, thu thap project_code | +50 |
| `static/index.html` | (khong doi - reuse combobox structure tu tab Processed) | 0 |
| `.gitignore` | them `gdd/` | +1 |
| `tests/test_gdd.py` (moi) | 4 unit + 5 integration tests | +120 |

## Data Model

### File `gdd/<CODE>.md`
- Markdown thuan
- Khong co schema cu the, AI doc hieu noi dung
- Vi du:
  ```markdown
  # GRPG - Game RPG Horus
  
  ## Tong quan
  Game RPG theo turn-based, target audience 18-35, mobile + PC.
  
  ## Tinh nang chinh
  - He thong nhan vat, ky nang, trang bi
  - PvE campaign, PvP arena
  - He thong gacha / IAP
  
  ## Quality bar
  - Moi task phai co the do luong duoc
  - Performance < 200ms input latency
  ```

## Cache strategy (in-memory)

```python
gdd_cache = {}  # {project_code: content or None}

def get_gdd(project_code):
    if project_code not in gdd_cache:
        path = os.path.join(BASE_DIR, "gdd", f"{project_code}.md")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                gdd_cache[project_code] = f.read()
        else:
            gdd_cache[project_code] = None
    return gdd_cache[project_code]
```

- Load lazy: chi load khi gap project_code moi
- Khong co invalidation: neu GDD thay doi, restart app de refresh
- Cache miss: tra None, AI su dung nhu khong co GDD (silent skip)

## Edge cases

| Case | Xu ly |
|---|---|
| File `gdd/<code>.md` khong ton tai | skip, khong inject (silent) |
| 1 task co project, 1 task khong co | 400 validation (bat buoc ca 2) |
| Tat ca project deu co GDD | concat tat ca, AI dung dung GDD theo tung task |
| GDD file rong | skip, khong inject |
| GDD rat dai (>50K tokens) | canh bao console, van gui (AI tu truncate) |
| Cache miss lan dau | load file, luu vao dict |
| Cache hit | tra content ngay |
| User paste project_code khong hop le (khong co trong projects.json) | van xu ly duoc, GDD skip |

## Test cases

### Unit test (test_gdd.py)
1. `wrap_user_tasks_full` nhan gdd_map -> system prompt co chua GDD content
2. `wrap_user_tasks_full` khong co gdd_map -> system prompt KHONG co GDD section (backward compat)
3. `wrap_user_tasks_full` voi gdd_map co nhieu project -> concat theo format
4. Mock `call_ai_provider` verify call_args[0] (system_prompt) co GDD

### Integration test
5. `get_gdd` load file khi chua cache
6. `get_gdd` tra cache khi da load (khong doc file lan 2)
7. `get_gdd` cho project khong co file -> None
8. `from_text_full` validation: task thieu project_code -> 400
9. `from_text_full` happy path: 2 task co project, GDD files ton tai -> AI nhan gdd_map
10. Endpoint `GET /api/projects/GRPG/gdd` tra ve content (200)
11. Endpoint `GET /api/projects/NONEXIST/gdd` tra 404

## Done when

- [ ] Spec file duoc commit
- [ ] `.gitignore` co `gdd/`
- [ ] `wrap_user_tasks_full` them gdd_map, 4 unit test pass
- [ ] `get_gdd` + cache + endpoint, 5 integration test pass
- [ ] Frontend form row co combobox project, validate, payload co project_code
- [ ] Tat ca test cu van pass
- [ ] Version bump 1.0.31
