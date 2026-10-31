# Mẫu comment

Mặc định `language: vi`, `voice: a/anh` (người nói là `a`, gọi tác giả là `anh`).

Trước khi đăng hoặc in: thay giọng và ngôn ngữ theo config. `language` khác `vi` thì dịch cấu trúc này, không giữ tiếng Việt. Không thêm lời khen. Không câu nào không có bằng chứng ở báo cáo.

Finding loại bỏ thì một dòng lý do, không giải thích dài.

```markdown
## Review chấm điểm — <issue-id hoặc "không có issue"> / PR #<number>

**Điểm tổng: X / 10**
**Verdict:** Có thể merge | Nên sửa trước khi merge | Chưa nên merge

cc @<author> a đã review xong. <một câu: còn finding cần xem, hoặc có thể merge>.

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

Verdict:

| Điều kiện | Verdict |
|---|---|
| ≥ ngưỡng merge, không blocker, không important, test bắt buộc không fail | Có thể merge |
| Không blocker, nhưng dưới ngưỡng hoặc còn important | Nên sửa trước khi merge |
| Còn blocker, hoặc test bắt buộc fail | Chưa nên merge |

Câu mở khi chưa merge: `cc @<author> a đã review xong, còn finding bên dưới, chưa merge, xem lại giúp a.`

Câu mở khi merge được: `cc @<author> a đã review xong, điểm X/10, có thể merge.`

Đổi `a` / `anh` theo `voice`. Không giữ "a" nếu config đặt giọng khác.
