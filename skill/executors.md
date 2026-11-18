# Executor

Parent giữ intake, đọc diff, kiểm chứng cuối, chấm điểm, và mọi thao tác ghi. Auditor không sửa repo, không comment, không merge.

Audit chéo bắt buộc hai model khác họ. Họ là dòng model của nhà cung cấp (vd. Claude và GPT), không phải chuỗi id: khác mức effort, hay hai bản của cùng một dòng, không tính.

## Mặc định: parent + một auditor phụ

Khi skill chạy trong một luồng chính đang sống (session có model riêng), luồng chính **là auditor A**. Chỉ spawn **một** auditor phụ khác họ model làm auditor B. Không spawn thêm subagent cùng họ với parent — tốn token, không thêm góc nhìn.

- Auditor phụ: CLI `audit.secondary_cli` (mặc định `codex`). Model theo thứ tự: model người dùng nêu trong chat (vd. "review với gpt-6.1-sol") → `audit.secondary_model` → key `model` cấp cao trong `config.toml` của Codex (`$CODEX_HOME`, mặc định thư mục `.codex` trong home). Vẫn không có → hỏi một lần. Model mặc định của Codex có thể khác model người dùng muốn; không lặng lẽ rơi về mặc định khi chat đã nêu model.
- Parent khác họ với auditor phụ là điều kiện bắt buộc. Cùng họ → chọn auditor phụ khác hoặc hỏi một lần.
- Vòng 1 chạy song song: spawn auditor phụ ở background trước, rồi parent tự review full diff. Parent **ghi log finding của mình vào `$work/a-r1.yaml` theo hợp đồng vòng 1 trước khi đọc log auditor phụ**. Không sửa file đó sau khi đã đọc log kia.
- Vòng 2: auditor phụ nối tiếp đúng phiên vòng 1 và nhận log của parent. Parent tự audit log của auditor phụ theo hợp đồng vòng 2, ghi phán quyết từng finding.
- Parent vẫn giữ vai tổng hợp cuối và bước đọc lại `file:line`. Finding mà chỉ parent tìm và chỉ parent `accept` không đủ: cần auditor phụ `accept`, hoặc parent ghi rõ vì sao lời `reject` của phụ sai.

### Kiểm auditor phụ trước — parent, trước khi tải input

`audit.preflight` (mặc định true): một lượt rất ngắn, tốn một ít quota, để biết sớm model có chạy không.

```bash
echo "Reply OK" | codex exec --sandbox read-only --skip-git-repo-check -m "$model" --json - 2>/dev/null \
  | jq -r 'select(.type=="error" or .type=="turn.failed") | .message // .error.message' | head -n1
```

In ra gì → auditor phụ không chạy được (model không hỗ trợ, hết hạn mức…): in nguyên văn, sang bảng Fallback. Không tải input, không chấm. Mã thoát của `codex exec` không đủ tin; luôn đọc sự kiện lỗi trong JSONL, ở cả vòng 1 và 2.

### Chuẩn bị input — parent, một lần, ngoài repo

Auditor không gọi mạng. Mỗi lệnh mạng trong sandbox read-only phải xin quyền, và mỗi lần đọc file qua `gh api` mất khoảng 5–17s; đọc tuần tự từng file như vậy là nguyên nhân chính làm auditor chậm. Parent tải sẵn mọi thứ vào `$work`:

```bash
work="${TMPDIR:-/tmp}/pr-orchestrator/<owner>-<repo>-<n>-<sha7>[_<n>-<sha7>…]"   # cố định để chạy tiếp được; nhiều PR nối bằng _
mkdir -p "$work"
gh pr diff <n> --repo <slug> > "$work/pr<n>.diff"          # lặp cho mỗi PR trong lần gọi
gh pr view <n> --repo <slug> --json number,title,body,author,baseRefName,headRefOid,isDraft,commits,files > "$work/pr<n>.json"
gh api "repos/<slug>" --jq .size        # KB
mkdir "$work/head<n>"
gh api "repos/<slug>/tarball/<headRefOid>" > "$work/head<n>.tgz" \
  && tar -xzf "$work/head<n>.tgz" -C "$work/head<n>" --strip-components=1
```

`pr<n>.json` `.headRefOid` phải bằng `<headRefOid>` dùng cho tarball. Khác → PR vừa có commit mới: làm lại intake, không trộn diff của head này với snapshot của head khác.

Repo lớn hơn 100000 KB, hoặc tarball lỗi: không tải tarball. Parent chỉ kéo các file trong diff (bỏ file có `changeType` là `DELETED` trong `pr<n>.json`) và các file rule đã đọc, vào đúng đường dẫn dưới `$work/head<n>`:

```bash
mkdir -p "$(dirname "$work/head<n>/<path>")"
gh api "repos/<slug>/contents/<path>?ref=<headRefOid>" --jq .content > "$work/b64" \
  && base64 -d < "$work/b64" > "$work/head<n>/<path>"
```

`gh api` lỗi, hoặc file ra rỗng trong khi diff có dòng thêm → dừng, không chạy auditor trên snapshot thiếu. File lớn hơn 1 MB không có `.content` qua API này: ghi vào prompt là file đó chỉ có trong diff.

Cần so với base: kéo file base tương ứng vào `$work/base<n>` theo cùng cách, với `ref=<baseRefName>`.

`$work` nằm ngoài repo; đây là file tạm duy nhất `review` được ghi. Prompt vòng 1 và 2 cũng để ở `$work`.

`$work` đã có `state.json` (từ lần bị chặn trước) và `headRefOid` vẫn khớp → dùng lại input và `a-r1.yaml`, không viết lại log của parent; chỉ chạy phần auditor phụ còn thiếu. Head khác → thư mục mới, làm lại intake.

### Gọi Codex

```bash
codex exec --sandbox read-only --skip-git-repo-check -C "$work" -m "$model" \
  --json -o "$work/b-r1.md" - < "$work/prompt-r1.md" > "$work/b-r1.jsonl" 2> "$work/b-r1.err" &
b_pid=$!
# parent review full diff, ghi $work/a-r1.yaml, rồi mới chờ B
wait "$b_pid" || { echo "auditor B lỗi: $work/b-r1.err"; exit 1; }   # dừng, sang bảng Fallback; không resume
thread=$(jq -r 'select(.type=="thread.started") | .thread_id' "$work/b-r1.jsonl" | head -n1)

codex exec resume "$thread" --skip-git-repo-check -m "$model" -c 'sandbox_mode="read-only"' \
  -o "$work/b-r2.md" - < "$work/prompt-r2.md" > /dev/null 2> "$work/b-r2.err"
```

- Vòng 1 chạy nền (`&`). Shell của tool không giữ job giữa các lần gọi thì chạy lệnh vòng 1 bằng chế độ nền/async của tool thay cho `&` + `wait`. Câu trả lời cuối nằm ở `-o`. `thread_id` lấy từ sự kiện `thread.started` trong JSONL. B lỗi → theo bảng Fallback, không chấm bằng một auditor.
- Vòng 2 dùng `resume`, không mở phiên mới: auditor giữ những gì đã đọc ở vòng 1, không đọc lại từ đầu. `resume` không có cờ `--sandbox`, nên phải truyền `-c 'sandbox_mode="read-only"'`.
- `-m` luôn truyền. Auditor không tự biết model id của nó (tự khai sai, vd. "gpt-6" khi chạy `gpt-6.1-sol`). Model thật lấy từ rollout của phiên, sau mỗi vòng:

  ```bash
  f=$(find "${CODEX_HOME:-$HOME/.codex}/sessions" -name "rollout-*-$thread.jsonl" | head -n1)
  jq -r 'select(.type=="turn_context") | "\(.payload.model) \(.payload.effort)"' "$f" | sort -u
  ```

  Phải đúng model đã chọn. Khác, hoặc không tìm thấy rollout → ghi rõ, không ghi model id theo `-m`. Parent điền model thật vào log của B.
- `audit.codex_ignore_user_config: true` → thêm `--ignore-user-config` vào cả hai lệnh. Cờ này bớt 3–9s khởi động (MCP, plugin, hook), nhưng bỏ luôn provider, profile, `service_tier` của người dùng. Mặc định tắt.
- Không có `jq`: lấy `thread_id` từ dòng `{"type":"thread.started",...}` đầu tiên của JSONL.

Trước vòng 1 và sau vòng 2, `git status --porcelain` của repo phải giống nhau. Khác trong `review` → dừng, không revert.

Chỉ dùng hai auditor riêng (mục "Chọn đường" dưới) khi config đặt `audit.mode: two`, hoặc người dùng yêu cầu.

## Chọn đường (mode `two`)

`audit.via` trong config: `omp`, `orca`, hoặc `auto`. Mặc định `auto`.

1. `audit.models` có đủ hai selector khác họ model → dùng đúng cặp đó.
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

Cùng input cho mọi auditor, theo [templates/prompt-r1.md](templates/prompt-r1.md): mỗi PR `pr<n>.diff`, `pr<n>.json` (body, commit kèm message), snapshot `head<n>/` (và `base<n>/` nếu có), rule repo đã đọc, config nếu có. Auditor đọc file local, không gọi mạng. Mẫu giữ nguyên lệnh cấm và YAML output; không viết lại tay.

Parent không biết model id đã chạy, hoặc hai log cùng họ model → huỷ cặp, chọn lại. Không chấm trên cặp đó.

`introduced_by_pr: unknown` không được trừ điểm. Parent xác minh hoặc để ngoài điểm.

## Hợp đồng vòng 2 — audit cách làm, không audit cảm tính

Mỗi auditor đọc lại dòng bên kia đã trích. Với từng finding:

| Phán quyết | Khi nào |
|---|---|
| `accept` | Cách tìm có đường, dòng trích chứa đúng claim, kiểm chứng tái hiện được, không lẫn lỗi có từ trước |
| `reject` | Sai dòng, lệnh không thể ra claim đó, coi lỗi cũ là lỗi PR, bỏ caller bắt buộc, trái rule repo đã nêu |
| `unverified` | Claim có thể đúng nhưng log không đủ để kiểm lại |

Không thêm finding mới ở vòng 2. Finding mới chỉ từ vòng 1 hoặc từ parent sau khi parent tự kiểm chứng và ghi nguồn `parent`.

Prompt và YAML phán quyết: [templates/prompt-r2.md](templates/prompt-r2.md).

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
| Auditor phụ hết hạn mức, hoặc model không chạy | Không chấm bằng một auditor, không thử lại vòng lặp. Ghi `$work/state.json` (`{pr, head, model, done: [...], error, a_r1}`) và in lỗi nguyên văn (có giờ reset nếu Codex báo). Có `audit.backup_model` khác họ với parent → hỏi một lần có dùng không; không có → hỏi chờ hay đổi model |
| Auditor sửa tree trong `review` | Dừng. Báo file. Không dọn |
| Lệnh test không khám phá được | Ghi "chưa chạy được". Không bịa lệnh, không bịa kết quả |
