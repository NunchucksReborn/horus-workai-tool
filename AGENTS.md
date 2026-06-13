# Workflow cho horus-workai-tool (medium project, 1-2 tuần)

## Quy tắc tìm kiếm web (luôn áp dụng)

Khi cần tra cứu thông tin trên web (docs, libraries, news, error messages, best practices...), **luôn ưu tiên dùng `MiniMax_web_search`** (Token Plan MCP của MiniMax) thay vì `webfetch` trực tiếp.

- Cần search nhiều → dùng `MiniMax_web_search` để có danh sách URL liên quan
- Có URL cụ thể rồi → dùng `webfetch` để đọc chi tiết
- Kết hợp cả 2: search trước → fetch nội dung top kết quả → tổng hợp

Không tự suy luận kiến thức từ training data khi có thể search real-time.


Project solo, có test framework, ceremony vừa phải — nặng hơn Tier 2 nhưng nhẹ hơn superpowers gốc.

**Cách bắt đầu:** Mở OpenCode trong folder này, nói:
- *"Setup project theo Phase 0"* (lần đầu)
- *"Bắt đầu feature [tên]"* (từ lần 2 trở đi)
- *"Check bug [mô tả]"* (khi cần investigate)

## Quy tắc chung (luôn áp dụng)
- KHÔNG hỏi "tiếp nhé?" giữa chừng — làm liên tục đến khi xong
- KHÔNG dispatch subagent — solo, tự handle
- TDD luôn: RED → verify fail → GREEN → verify pass → commit
- Test framework đã setup → PHẢI viết test cho mỗi behavior mới
- Mỗi feature = 1 worktree, 1 commit khi GREEN
- Cuối mỗi phase: self-review 1 lần

---

## Phase 0: Project bootstrap (chạy 1 lần đầu)

1. **Init git**: `git init`, tạo `.gitignore` (node_modules, dist, .env, .worktrees, v.v.)
2. **Chọn test framework** theo stack (sẽ quyết trong brainstorm):
   - Node.js / TypeScript → `vitest` (khuyến nghị) hoặc `jest`
   - Python → `pytest`
   - Go → built-in `testing`
3. **Setup structure** chuẩn:
   ```
   horus-workai-tool/
   ├── src/          # source code
   ├── tests/        # test files (mirror src/)
   ├── docs/
   │   └── specs/    # feature specs
   ├── package.json  # hoặc pyproject.toml, go.mod
   └── README.md
   ```
4. **Add scripts**:
   - `npm test` / `pytest` / `go test ./...` — chạy test
   - `npm run dev` — chạy tool ở dev mode (nếu cần)
5. **Hello-world test PASS** để verify framework hoạt động
6. **Commit**: `chore: bootstrap project with <framework>`

---

## Phase 1: Mini-spec (cho mỗi feature mới)

**Khi nào:** Feature multi-day, > 1 file, hoặc có API surface mới.

1. **Brainstorm 3-5 câu** trong chat (input/output, edge case, error handling)
2. **Design inline** (~20-30 dòng) trong chat, gồm:
   - Goal (1 câu)
   - API/interface (function signatures, classes)
   - File structure (file nào làm gì)
   - Edge cases cần handle
3. **Save spec** → `docs/specs/YYYY-MM-DD-<feature>.md` (1-2 trang, lightweight)
4. **Self-review spec** — check placeholder, internal consistency
5. **Move to Phase 2**

Commit: `docs: spec for <feature>`

### Spec template

```markdown
# [Feature Name]

## Goal
[1 câu mô tả feature làm gì]

## API
- `foo(input: Type): ReturnType` — mô tả ngắn
- `bar(): void` — mô tả ngắn

## Files
- `src/<feature>.ts` — main logic
- `tests/test_<feature>.test.ts` — tests

## Edge cases
- Empty input → ...
- Invalid input → ...
- ...

## Done when
- [ ] All edge cases có test
- [ ] Test coverage > 80% cho feature này
- [ ] README updated (nếu user-facing)
```

---

## Phase 2: Plan (compressed)

1. **Tạo worktree** cho feature:
   ```bash
   git worktree add .worktrees/<feature> -b feat/<feature>
   cd .worktrees/<feature>
   ```
2. **Verify baseline** test pass trước khi start
3. **`todowrite` 5-10 task**, mỗi task có:
   - Files sẽ touch (path cụ thể)
   - Done criteria (pass test nào)
4. **Move to Phase 3**

---

## Phase 3: Implementation (per task, TDD cycle)

Cho MỖI task trong todowrite:

1. **RED — Write failing test** trong `tests/`:
   - Test 1 behavior, clear name
   - Run test → **verify FAIL đúng lý do** (không phải typo)
2. **GREEN — Write minimal impl** trong `src/`:
   - Đủ để pass test, không over-engineer
   - Run test → **verify PASS + all tests still pass**
3. **REFACTOR** (nếu cần): clean up, giữ test green
4. **Commit** (gộp test + impl trong 1 commit):
   ```
   feat(<feature>): <task-name>

   - Add test for <behavior>
   - Implement <minimal code>
   ```
5. **Self-review 1 lần** cho task này
6. **Next task** (lặp lại từ 1)

**Quy tắc TDD cứng — KHÔNG vi phạm:**
- Code mà không có test trước → **XÓA**, làm lại từ test
- Test pass ngay = test không test cái mới → **viết lại**
- "Skip TDD just this once" = red flag → **DỪNG**
- 3 lần fix fail liên tiếp → **dừng lại**, question design (không fix tiếp)

---

## Phase 4: Integration

Khi tất cả task trong todowrite xong:

1. **Full test suite** — chạy toàn bộ, **verify 100% pass**
2. **Self-review toàn bộ**:
   - Code clean? (no debug log, no commented code, no TODO)
   - Spec coverage? (mỗi requirement đã có test)
   - Edge case đã handle hết?
3. **Lint check** (nếu có): `npm run lint` hoặc tương đương
4. **Commit cleanup** nếu có: `chore: clean up before merge`

---

## Phase 5: Finish

1. **Verify tests** lần cuối trong worktree
2. **Merge về main** (chạy từ main repo, KHÔNG phải trong worktree):
   ```bash
   cd /run/media/system/home/Horus/horus-workai-tool
   git checkout main
   git merge feat/<feature>
   git worktree remove .worktrees/<feature>
   ```
3. **Chọn option**:
   - **Merge xong, dừng** (solo, không cần push)
   - **Push** (nếu có remote): `git push origin main`
   - **Keep worktree** (nếu chưa xong thật sự)
   - **Discard** (nếu sai hướng): xác nhận trước, rồi `git worktree remove` + `git branch -D`

---

## Bug check trong project

Dùng **Tier 1A từ `yt-translator/AGENTS.md`** (reproduce → isolate → bug report → gửi). Không cần bug check template riêng ở đây.

---

## Dấu hiệu lệch hướng (nhắc agent ngay)

| Agent làm gì | Bạn nên nói |
|---|---|
| Phase 3 mà skip RED (code trước test) | "TDD iron law, làm lại từ test" |
| Phase 3 mà commit test pass ngay | "Test không test cái mới, viết lại" |
| Phase 3 fix 3 lần vẫn fail | "Dừng, question design trước khi fix tiếp" |
| Phase 1 mà brainstorm 5+ câu | "Gộp lại, tier này 3-5 câu max" |
| Agent tự merge code trong Phase 5 | "DỪNG, confirm option trước" |
| Agent propose subagent | "Solo, tự handle" |
| Agent ghi file plan (docs/plans/...) | "Skip, dùng todowrite" |
| Agent bỏ qua test framework | "Setup vitest/pytest trước, rồi mới code" |
| Agent dùng `--no-verify` hoặc skip test | "KHÔNG BAO GIỜ skip test" |
