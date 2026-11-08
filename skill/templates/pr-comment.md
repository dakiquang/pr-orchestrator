# Mẫu comment

Mặc định `language: vi`, `voice: a/anh` (người nói là `a`, gọi tác giả là `anh`).

Trước khi đăng hoặc in: thay giọng và ngôn ngữ theo config. `language` khác `vi` thì dịch cấu trúc này, không giữ tiếng Việt. Không thêm lời khen. Không câu nào không có bằng chứng ở báo cáo.

Finding loại bỏ thì một dòng lý do, không giải thích dài.

## PR của chính mình

`self_review` (SKILL.md mục 1) là true → vẫn chấm, vẫn đưa finding, vẫn đăng nếu người gọi yêu cầu. Khác PR thường:

- Bỏ dòng `cc @<author> …`. Không mention tác giả.
- Không câu "đã review xong", "xem lại giúp".
- Không đại từ ở bất kỳ mục nào, kể cả "Nguồn review" và "Đã loại". Viết câu không chủ ngữ: "Đã loại", "Đã đọc lại dòng được trích".
- Câu mở thay bằng một dòng: `Điểm X/10 — <verdict>. <còn N finding cần sửa | không còn finding chặn merge>.`

`voice` không áp cho PR của chính mình.

## Mẫu

```markdown
## Review chấm điểm — <issue-id hoặc "không có issue"> / PR #<number>

**Điểm tổng: X / 10**
**Verdict:** Có thể merge | Nên sửa trước khi merge | Chưa nên merge

<câu mở — xem cuối file>

### Nguồn review
- **Auditor:** <model A> và <model B> — audit chéo cách tìm và cách kiểm chứng. Bất đồng: <ngắn, hoặc không>
- **Parent:** đã đọc lại dòng được trích trước khi cho vào điểm
- **Rule / issue:** <path rule đã áp, id issue, hoặc "không lấy được issue — chấm theo mô tả PR">
- **CI:** <trạng thái gh pr checks. Không ghi là test local nếu chưa chạy>

### Cổng merge
- Blocker: <số, file:line, hoặc không>
- Important còn lại: <số, hoặc không>
- Test / CI: <đã chạy lệnh nào + exit, hoặc "chưa chạy local"; CI riêng>
- Trần điểm: <trần đã áp, hoặc không>
- Mergeable: <trạng thái>

### Yêu cầu ↔ diff
<!-- Bỏ cả mục nếu không có issue và không có acceptance trong mô tả PR. -->

| Yêu cầu | Diff | Kết quả |
|---|---|---|
| <điều kiện> | <file hoặc "không có"> | đạt / chưa / ngoài scope |

### Bảng điểm
<!-- Một hàng cho mỗi hạng của rubric đã áp, đúng tên và trọng số. Dưới đây là rubric mặc định. -->

| Hạng mục | Trọng số | Điểm | Bằng chứng |
|---|---:|---:|---|
| Đúng đắn / bảo mật / blocker | 35% | … | … |
| Yêu cầu / acceptance | 25% | … | … |
| Chất lượng và kiến trúc | 15% | … | … |
| Test và kiểm chứng | 15% | … | … |
| Phạm vi và bảo trì | 10% | … | … |

### Finding
<!-- Đánh số, blocker trước, rồi important, rồi nit. Chỉ finding đã kiểm chứng và do PR gây ra. -->

1. **[blocker|important|nit]** `file:line` — vấn đề. Hệ quả: … Cách sửa: …

### Không chặn merge
- <nit đã kiểm chứng, hoặc lỗi có từ trước không trừ điểm, hoặc head chậm hơn base>

### Đã loại
- <id> `file:line` — <sai / có từ trước / chưa kiểm chứng được / auditor reject đúng>

### Kết luận
<1–2 câu. Có merge được không, và vì cổng nào.>
```

Verdict lấy theo bảng Verdict trong [gates.md](../gates.md). Không tự đặt điều kiện khác.

## Câu mở

PR của người khác:

- Chưa merge được: `cc @<author> a đã review xong, còn finding bên dưới, chưa merge, xem lại giúp a.`
- Merge được: `cc @<author> a đã review xong, điểm X/10, có thể merge.`

Đổi `a` / `anh` theo `voice`. Không giữ "a" nếu config đặt giọng khác.

PR của chính mình: dòng trung tính ở mục "PR của chính mình", không cc, không đại từ.
