---
name: pr-orchestrator
description: >-
  Điều phối review pull request dùng chung mọi repo: hai model khác nhau audit
  chéo cách tìm và kiểm chứng, rồi chấm điểm. Tuỳ mode mới sửa nhỏ, test,
  comment, merge, release, hoặc sync. Dùng khi người dùng gọi /pr-orchestrator
  hoặc yêu cầu review, chấm điểm, sửa finding, comment, merge, hay đồng bộ một
  PR. Không gắn repo, package manager, runtime, hay tên nhánh.
---

# PR Orchestrator

Skill dùng chung. Không có repo mặc định, không có package manager mặc định, không có nhánh base mặc định, không có lệnh test mặc định.

Đọc hết các file này trước khi kết luận:

1. [executors.md](executors.md) — hai model audit chéo; omp hoặc orca
2. [gates.md](gates.md) — trần điểm, cổng merge, vòng sửa
3. [templates/pr-comment.md](templates/pr-comment.md) — mẫu comment
4. `.pr-orchestrator.yml` ở gốc repo, nếu có. Mẫu nằm cạnh skill này: `config.example.yml`. Không tự tạo file đó trong repo.

Mọi đường dẫn tương đối ở trên nằm trong thư mục skill (`skill://pr-orchestrator/...`).

## Luật nào thắng

Luật repo thắng skill này. Đọc những file tồn tại, theo thứ tự:

1. `AGENTS.md`, `CLAUDE.md`, `REVIEW.md`
2. `.cursor/rules/`
3. `docs/rules/`, `CONTRIBUTING.md`
4. Skill cục bộ của repo (`.omp/skills/`, `.agents/skills/`, `.claude/skills/`, `.codex/skills/`)

Rubric hoặc skill chấm điểm của repo ghi đè rubric mặc định khi nó nói rõ trọng số. Vẫn trích rule cụ thể khi trừ điểm. Không bịa rule.

## Mode

| Mode | Việc làm | Được thay đổi |
|---|---|---|
| `review` | intake đọc → audit chéo → kiểm chứng → chấm | không |
| `fix` | review → sửa nhỏ nhất → test → chấm lại một lần | có, trong phạm vi finding |
| `full` | review → fix → test → comment → merge đúng PR này | có |
| `test` | tìm và chạy test liên quan | chỉ chạy test |
| `sync` | đưa commit đã merge sang nhánh `--target` | có, chỉ cherry-pick |

Chỉ đưa PR, không nêu mode → `review`.

`full` chỉ cho phép, với đúng PR này: push commit sửa, comment điểm, merge. Đóng PR khác, tạo release, sửa body PR, force-push, xoá nhánh: cần một câu riêng trong chat này. Một lần đồng ý không áp dụng cho việc khác, PR khác, hay nhánh khác.

## An toàn

- `review` là read-only. Không checkout, fetch, stash, commit, push, comment, merge, sửa file, tạo worktree, tạo nhánh. Danh sách lệnh được phép nằm ở mục Intake.
- Worktree bẩn: không tự stash. `fix` / `full` / `test` dừng và hỏi nếu checkout sẽ đè thay đổi chưa commit. `review` vẫn đọc PR từ xa, và ghi nhận worktree bẩn.
- Không `--no-verify`, force-push, reset huỷ diễn, commit secret, xoá nhánh nếu người dùng không yêu cầu.
- Không thêm dòng tác giả, `Co-Authored-By`, hay "Generated with" của AI. Chỉ thêm nếu convention của repo bắt buộc và config không cấm. Mặc định là không thêm.
- Stash chỉ khi người dùng buộc dùng, và chỉ ngoài `review`: `git stash push -m <tag>`, lấy SHA, `git stash apply <sha>`, drop theo tag. Không `git stash` trần, không `pop`.
- Sửa thẳng working tree để người dùng tự test: không commit. Nói rõ nhánh và file.
- Sau auditor, `git status --porcelain` phải giống lúc bắt đầu `review`. Nếu khác: dừng, báo file đổi. Không revert, không stash.

## 0. Khám phá — không đoán

Lấy từ repo hoặc config. Thiếu và không suy được từ file thì hỏi một lần, hoặc ghi "chưa chạy được". Không bịa lệnh.

| Việc | Nguồn |
|---|---|
| Repo slug | URL PR, hoặc `gh repo view --json nameWithOwner`, hoặc `git remote get-url origin` |
| Base | `baseRefName` của PR. Không điền tên nhánh nếu metadata không có |
| Head | `headRefOid` / `headRefName` của PR |
| Lệnh test, typecheck, lint | config `commands` → workflow CI → script manifest / Makefile / tài liệu đóng góp. Không chọn sẵn một trình quản lý gói |
| Package manager, runtime | lockfile, trường package manager, file version, `engines`. Đọc giá trị thật |
| Ngôn ngữ comment, giọng | config `language` (mặc định `vi`), `voice` (mặc định `a/anh` = người nói `a`, người được gọi `anh`) |
| Auditor | config `audit.models` nếu có đúng hai model khác họ; không thì khám phá theo [executors.md](executors.md) |
| Đường cấm sửa | chỉ `protected_paths` trong config. Không có danh sách mặc định |

Config thiếu field → dùng mặc định của skill, rồi vẫn khám phá lệnh và nhánh như trên.

## 1. Intake

Tách args: mode, PR (URL hoặc số), `--target`, `--filter`. `--wait` / `--background` chỉ là gợi ý chờ auditor, không mở thêm quyền sửa.

Đọc PR:

```bash
gh pr view <pr> --repo <slug> --json number,title,body,author,baseRefName,headRefName,headRefOid,state,url,mergeable,mergeStateStatus,additions,deletions,changedFiles,files,commits,reviews,comments,statusCheckRollup
gh pr diff <pr> --repo <slug>
gh pr checks <pr> --repo <slug>
```

`gh pr checks` là trạng thái CI từ xa, không phải "đã chạy test local".

So sánh head với base bằng API đọc, không fetch:

```bash
gh api repos/<slug>/compare/<baseRefName>...<headRefOid> --jq '{status,ahead_by,behind_by}'
```

Ghi nếu head chậm hơn base. Không cập nhật nhánh.

`review` dừng ở đây về git. Không tạo `pr-<n>-review`.

`fix` / `full` / `test` mới được tạo nhánh local, và chỉ sau khi `git status --porcelain` rỗng. Không rỗng → dừng, hỏi, không stash.

Trước fetch, kiểm tra ref `pr-<n>-review`. Đã tồn tại mà người dùng không bảo ghi đè → dừng và hỏi. Không reset nhánh review cũ.

```bash
git fetch origin pull/<n>/head:pr-<n>-review
git checkout pr-<n>-review
```

`test` không commit. `sync` không dùng bước checkout này; xem mục 8.

## 2. Yêu cầu nghiệp vụ

Tìm issue từ body PR, tên nhánh, message commit, link bot. Tracker: config `issue_tracker`, không thì nhận từ URL (GitHub issue, Linear, Jira).

Lấy được: bảng yêu cầu ↔ diff (đạt / chưa / ngoài scope), mỗi dòng trỏ file hoặc "không có trong diff".

Không lấy được (chưa auth, không quyền, không có link): nói rõ. Chấm theo mô tả PR. Không bịa acceptance criteria.

## 3. Review và audit chéo

Parent đọc toàn bộ diff song song với hai auditor. Không giao diff rồi bỏ qua.

Hai auditor là hai model khác họ (khác model id, không chỉ khác mức effort). Chúng audit lẫn nhau về cách tìm và cách kiểm chứng, không chỉ về kết luận.

Mặc định: luồng chính là auditor A, cộng **một** auditor phụ khác họ (Codex CLI headless). Parent ghi log của mình trước khi đọc log phụ. Hai auditor riêng (omp/orca) chỉ khi `audit.mode: two` hoặc người dùng yêu cầu. Chi tiết: [executors.md](executors.md).

Một model, hoặc hai lần cùng model: không phải audit chéo. Không chấm như thể đã có hai model. Hỏi một lần model thứ hai, hoặc dừng phần điểm dual-audit và nói rõ.

Finding của auditor chỉ vào điểm sau khi parent đọc lại đúng dòng đã trích, hoặc chạy lại lệnh đọc đã trích. Đồng ý của cả hai không thay bước đó.

## 4. Kiểm chứng thêm — parent, read-only khi đang `review`

Với mỗi finding còn sống:

- Đọc caller, route, reducer, test quanh dòng đó, từ head SHA của PR (`gh api repos/<slug>/contents/<path>?ref=<headRefOid>` hoặc `git show <sha>:<path>` nếu object đã có local). Grep working tree chỉ là bằng chứng nếu HEAD local đúng là head của PR. Nếu không, nói rõ và không dùng grep đó để kết tội PR.
- Cùng mẫu ở chỗ khác trong đúng revision của PR.
- Hồi quy so với base: dòng base mất khi giải conflict, hoặc hành vi base bị đổi ngoài yêu cầu.
- Commit không liên quan lẫn trong PR.
- Secret, file env bị commit.
- Convention commit của repo, gồm cấm attribution AI nếu repo hoặc config cấm.
- Test có lệnh chạy được không. `review` không chạy lệnh đó.

Tách "do PR gây ra" và "có từ trước". Chỉ trừ điểm phần do PR gây ra. Phần có từ trước ghi riêng, không trừ.

Finding loại: một dòng lý do (sai, có từ trước, thiếu ngữ cảnh, lệnh không tái hiện được).

## 5. Kiểm tra thật

Chỉ `test` / `fix` / `full`.

Chạy test của phần diff, typecheck lọc theo file đổi, lint chỉ xét dòng mới. Lệnh lấy từ mục 0. Không rõ → ghi "chưa chạy được", không bịa output.

Lỗi đã có trên base là baseline. Lỗi mới do PR mới trừ điểm. Không viết "đã test" nếu lệnh chưa chạy và chưa có output.

`review`: không chạy test, lint, hay typecheck nếu lệnh có thể ghi cache, build, hoặc lockfile. Trạng thái CI lấy từ `gh pr checks` và ghi là CI, không ghi là test local.

## 6. Chấm

Rubric mặc định, mỗi hạng 0–10, rồi nhân trọng số:

| Hạng | Trọng số |
|---|---:|
| Đúng đắn / bảo mật / blocker | 35% |
| Yêu cầu / acceptance | 25% |
| Chất lượng và kiến trúc | 15% |
| Test và kiểm chứng | 15% |
| Phạm vi và bảo trì | 10% |

Repo có rubric riêng thì dùng rubric đó. Làm tròn 0.5 sau khi cộng. Trần điểm trong [gates.md](gates.md) áp sau khi làm tròn; trần thắng nếu làm tròn vượt trần.

Không trừ hai lần cho cùng một finding.

## 7. Quyết định

Áp [gates.md](gates.md).

- `review`: in báo cáo trong chat. Không đăng, không sửa.
- `fix`: sửa nhỏ nhất đúng finding đã kiểm chứng. Không refactor kèm. Test cho hành vi vừa sửa khi có lệnh test và viết test là khả thi. Chấm lại một lần. Còn kẹt cổng → dừng, hỏi.
- `full`: như `fix`, rồi comment và merge chỉ khi cổng mở và chat này đã gọi `full` cho PR này.
- `test`: báo lệnh, exit code, lỗi mới so với baseline. Không sửa để cho test xanh trừ khi mode là `fix` hoặc `full`.
- `sync`: mục 8.

## 8. Comment, merge, release, sync

Comment: điền [templates/pr-comment.md](templates/pr-comment.md) theo `language` và `voice`. Không khen thừa. Không câu nào vượt quá bằng chứng ở mục 3–5. Đăng bằng `gh pr comment` chỉ khi mode và chat cho phép. Body để ở file tạm ngoài repo.

Merge: `gh pr merge` theo `merge.method` trong config. Config không nói: đọc method repo cho phép (`gh repo view --json squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed`). Nhiều method đều được → hỏi một lần. Không `--delete-branch` trừ khi được yêu cầu.

Release, chỉ khi chat yêu cầu release:

- Squash nhiều PR vào một nhánh release: mỗi PR một commit, message theo convention repo, có số PR.
- Đọc lại head PR ngay trước squash. Có commit mới sau lần review → review lại phần mới, không squash mù.
- Note tiếng Việt (hoặc `language`) theo nhóm: Tính năng / Sửa lỗi / Lưu ý khi deploy (phụ thuộc backend, worker, biến môi trường, dependency bị gỡ).
- Tag trỏ đúng đầu nhánh release. Nhánh đổi sau đó → cập nhật cả note lẫn tag, và nói đã làm vậy.
- PR gốc còn mở có thể trùng: liệt kê và hỏi trước khi đóng.

Sync, chỉ khi có `--target` và chat gọi `sync`:

- Không giả định tên nhánh đích.
- `git cherry-pick -x` từng commit đã merge. Conflict → dừng, không force-push, không tự giải bằng cách bỏ code base.
