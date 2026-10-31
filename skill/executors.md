# Executor

Parent giữ intake, đọc diff, kiểm chứng cuối, chấm điểm, và mọi thao tác ghi. Auditor không sửa repo, không comment, không merge.

Audit chéo bắt buộc hai model khác họ. Khác mức effort của cùng model id không tính.

## Mặc định: parent + một auditor phụ

Khi skill chạy trong một luồng chính đang sống (session có model riêng), luồng chính **là auditor A**. Chỉ spawn **một** auditor phụ khác họ model làm auditor B. Không spawn thêm subagent cùng họ với parent — tốn token, không thêm góc nhìn.

- Auditor phụ mặc định: Codex CLI headless (`codex exec --sandbox read-only`), model theo config của Codex trên máy hoặc `audit.secondary`. Ghi model id thật nó báo.
- Parent khác họ với auditor phụ là điều kiện bắt buộc. Cùng họ → chọn auditor phụ khác hoặc hỏi một lần.
- Vòng 1 chạy song song: spawn auditor phụ ở background trước, rồi parent tự review full diff. Parent **ghi log finding của mình ra file theo hợp đồng vòng 1 trước khi đọc log auditor phụ**. Không sửa log đó sau khi đã đọc log kia.
- Vòng 2: auditor phụ nhận log của parent (một lần gọi nữa). Parent tự audit log của auditor phụ theo hợp đồng vòng 2, ghi phán quyết từng finding.
- Parent vẫn giữ vai tổng hợp cuối và bước đọc lại `file:line`. Finding mà chỉ parent tìm và chỉ parent `accept` không đủ: cần auditor phụ `accept`, hoặc parent ghi rõ vì sao lời `reject` của phụ sai.

Chỉ dùng hai auditor riêng (mục "Chọn đường" dưới) khi config đặt `audit.mode: two`, hoặc người dùng yêu cầu.

`self` trong config nghĩa là parent đọc full diff song song. Trong mode `two` đó không phải model thứ hai; trong `parent_plus_one` parent là auditor A.

## Chọn đường (mode `two`)

`audit.via` trong config: `omp`, `orca`, hoặc `auto`. Mặc định `auto`.

1. `audit.models` có đủ hai selector khác model id → dùng đúng cặp đó.
2. `omp` hoặc `auto`, và session có task tool biết `model`: khám phá role, spawn hai task read-only.
3. `orca` hoặc (`auto` mà bước 2 không tách được hai model): hai agent CLI khác nhau qua orca, trong worktree hiện tại, prompt read-only.
4. Không có orca: delegator headless trên `PATH` (tên lệnh khám phá được, không hard-code đường dẫn nhà). Hai `--to` khác nhau, prompt read-only.
5. Vẫn một model: hỏi một lần. Không bịa auditor thứ hai. Không chấm dual-audit.

`review` không tạo worktree git, không `orca worktree create`, không checkout. Orca chỉ được mở terminal agent trong worktree hiện tại, hoặc gọi headless.

Trước khi spawn và sau khi cả hai trả lời:

```bash
git status --porcelain
```

Khác nhau trong `review` → dừng. Không revert.

## Khám phá model trên omp

```bash
omp config get internal.modelRoles
```

Chọn hai role mà model id khác nhau, và khác model của parent nếu còn lựa chọn. Không ghi selector của máy này vào skill. Role không đọc được → hỏi một lần.

Spawn một lượt, song song, agent read-only (`scout`, hoặc agent review mà tài liệu session ghi là không ghi file). Mỗi task một `model`. Prompt vòng 1 giống hệt nhau và không chứa finding của ai.

Vòng 2, sau khi cả hai đã trả lời: spawn lại đúng hai model. A nhận log của B. B nhận log của A. Không đưa điểm parent đã nghĩ.

## Orca

Chỉ khi `orca status --json` chạy được. Không đổi executable orca giữa các lệnh.

Không `worktree create` trong `review`. Hai terminal, hai agent id đã cài và khác nhau:

```text
orca terminal create --worktree active --command "<agent>" --json
orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json
orca terminal send --terminal <handle> --text "<prompt vòng 1>" --enter --wait-submit 30 --json
```

`wait.satisfied` phải true trước send. Send chưa chứng minh turn đã bắt đầu thì không gửi lại. Đọc output bằng `orca terminal read`. Vòng 2 là một send nữa trên cùng terminal, kèm log của auditor kia.

Agent có thể vẫn ghi file dù prompt cấm. Porcelain đổi → dừng, coi pass đó không hợp lệ.

`fix` / `full` mới được tạo worktree riêng nếu cần cô lập sửa. `review` không.

## Headless

Chỉ khi omp task và orca đều không tách được hai model. Tìm binary delegator trên `PATH`. Không đoán đường dẫn tuyệt đối.

Hai lần gọi, hai đích khác nhau, prompt trên stdin, timeout đủ dài, không cờ quyền ghi thêm. Vòng 1 song song. Vòng 2 sau khi có cả hai log.

## Hợp đồng vòng 1

Cùng input: slug, số PR, URL, `baseRefName`, head SHA, diff hoặc lệnh `gh pr diff` để tự lấy, rule repo đã đọc (kèm path), config nếu có.

Cấm trong prompt: sửa file, checkout, fetch, stash, commit, push, comment, merge, tạo nhánh, tạo worktree.

Output bắt buộc:

```yaml
auditor:
  model: <model id thật sự chạy, không phải alias>
  method:
    commands: [{cmd, purpose, result_summary}]
    files_read: [{path, lines, why}]
    not_run: [{what, why}]
findings:
  - id: A1
    severity: blocker|important|nit
    introduced_by_pr: true|false|unknown
    file: path
    line: N
    claim: ...
    impact: ...
    fix: ...
    found_by: <lệnh tìm hoặc file đã mở trước khi kết luận>
    verified_by: <dòng đã đọc hoặc lệnh đã chạy lại>
    falsifier: <bằng chứng nào sẽ bác finding>
rejected_hypotheses:
  - claim: ...
    why_rejected: ...
```

Thiếu `model`, hoặc hai log cùng model id → huỷ cặp, chọn lại. Không chấm trên cặp đó.

`introduced_by_pr: unknown` không được trừ điểm. Parent xác minh hoặc để ngoài điểm.

## Hợp đồng vòng 2 — audit cách làm, không audit cảm tính

Mỗi auditor đọc lại dòng bên kia đã trích. Với từng finding:

| Phán quyết | Khi nào |
|---|---|
| `accept` | Cách tìm có đường, dòng trích chứa đúng claim, kiểm chứng tái hiện được, không lẫn lỗi có từ trước |
| `reject` | Sai dòng, lệnh không thể ra claim đó, coi lỗi cũ là lỗi PR, bỏ caller bắt buộc, trái rule repo đã nêu |
| `unverified` | Claim có thể đúng nhưng log không đủ để kiểm lại |

Không thêm finding mới ở vòng 2. Finding mới chỉ từ vòng 1 hoặc từ parent sau khi parent tự kiểm chứng và ghi nguồn `parent`.

Ô trống phương pháp là lỗi phương pháp, dù kết luận nghe hợp lý. `accept` không có `files_read` trỏ đúng claim → parent hạ xuống `unverified`.

## Parent tổng hợp

Vào điểm chỉ khi:

1. Parent đọc lại `file:line` trên revision head của PR, hoặc chạy lại lệnh đọc đã trích và output khớp claim.
2. Auditor kia không `reject` vì lý do parent xác nhận. Nếu kia `reject` mà parent vẫn thấy evidence: ghi vì sao lời reject sai, rồi mới giữ.
3. `introduced_by_pr` là true, đã đối chiếu base.

Cả hai `accept` mà parent không mở được dòng → không vào điểm. Ghi chưa kiểm chứng.

Bất đồng phương pháp ghi ngắn trong báo cáo. Không lấy trung bình điểm của hai model. Một điểm, của parent, sau cổng trên.

Finding parent tự thấy, không có trong hai log: được thêm nếu cùng chuẩn bằng chứng, nguồn ghi `parent`, và không nâng điểm chỉ vì parent thích.

## Việc parent không giao hết

Dù hai auditor im: secret, commit lạ, convention commit, mất code base khi giải conflict, cùng mẫu ngoài diff, CI từ `gh pr checks`. Các mục này vẫn là việc của parent ở SKILL.md mục 4.

## Fallback thiếu công cụ

| Thiếu | Làm |
|---|---|
| `gh` không auth | Dừng intake. Không review diff đoán từ thư mục local trừ khi người dùng đưa đúng head SHA và diff |
| Không có task tool | Sang orca, rồi headless |
| Orca không chạy | Không tự mở app để review. Sang headless hoặc hỏi |
| Một auditor timeout | Không chấm bằng auditor còn lại. Chạy lại auditor đó một lần, hoặc hỏi |
| Auditor sửa tree trong `review` | Dừng. Báo file. Không dọn |
| Lệnh test không khám phá được | Ghi "chưa chạy được". Không bịa lệnh, không bịa kết quả |
