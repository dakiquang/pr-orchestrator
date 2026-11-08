# Cổng

Rule repo và check bắt buộc của repo thắng file này. Ngưỡng merge là `merge.min_score` trong config, mặc định 8.0. Mọi chỗ dưới đây nói "ngưỡng" là giá trị đó.

File này là nơi duy nhất định nghĩa cổng merge, trần điểm và khung điểm. Template comment và SKILL.md dẫn chiếu tới đây, không định nghĩa lại.

## Cổng merge

Cổng mở khi tất cả đúng:

1. Điểm ≥ ngưỡng, tính sau trần.
2. Không còn blocker, và không còn finding important nào do PR gây ra (mọi loại, không chỉ đúng đắn hoặc bảo mật).
3. Test bắt buộc không fail. CI bắt buộc xanh nếu `merge.require_ci` là true. Mặc định `require_ci: false` — khi đó CI đỏ không tự chặn, nhưng phải ghi trạng thái thật, không ghi là xanh.
4. PR mở, mergeable, không conflict.
5. Không còn review request chưa giải mà repo coi là bắt buộc.
6. Head của PR vẫn là SHA đã review. Có commit mới → review lại phần mới trước.

Thiếu một điều → cổng đóng. Không hạ cổng để merge cho xong.

Cổng mở chỉ nói PR đạt về kỹ thuật. Được merge hay không còn cần quyền:

- Chỉ `full`, và chỉ đúng PR mà chat đã gọi `full`.
- Chat không thu hẹp thành review-only sau khi đã gọi `full`.
- `fix` không merge trừ khi chat cũng nói merge.

## Trần điểm

Áp sau khi làm tròn 0.5. Nhiều trần cùng áp thì lấy trần thấp nhất. Trần thắng nếu làm tròn vượt trần.

| Điều kiện do PR gây ra | Trần |
|---|---:|
| 1–2 blocker | 6.5 |
| ≥ 3 blocker | 5.0 |
| Còn finding important về đúng đắn hoặc bảo mật | 7.5 |
| Test bắt buộc fail vì PR | 7.5 |

Blocker có từ trước không kích trần. Ghi riêng.

Nit không kích trần, không chặn merge. Vẫn liệt kê.

Important không thuộc đúng đắn/bảo mật không kích trần, nhưng vẫn đóng cổng merge (điều 2).

## Khung điểm

Dùng để đối chiếu điểm đã cộng trọng số với finding còn lại. Mốc 8.0 là ngưỡng mặc định; config đặt ngưỡng khác thì mốc đó dịch theo.

| Khung | Finding do PR gây ra | Verdict |
|---|---|---|
| 9.0–10 | Không blocker, không important; nit ít hoặc không có | Có thể merge nếu cổng mở |
| 8.0–8.5 | Không blocker, không important; còn nit hoặc khoảng trống test nhỏ | Có thể merge nếu cổng mở |
| 7.0–7.5 | Còn important, hoặc dưới ngưỡng. Test bắt buộc fail (trần 7.5) → "Chưa nên merge" theo bảng Verdict | Nên sửa trước khi merge |
| 5.5–6.5 | 1–2 blocker | Chưa nên merge |
| ≤ 5.0 | ≥ 3 blocker, hoặc lệch yêu cầu chính | Chưa nên merge |

Điểm rơi ngoài khung ứng với finding → xem lại điểm từng hạng, rồi ghi lý do nếu vẫn giữ. Trần luôn thắng khung.

## Verdict

| Điều kiện | Verdict |
|---|---|
| Cổng merge mở (mục Cổng merge, điều 1–6) | Có thể merge |
| Không blocker, test bắt buộc không fail, nhưng cổng đóng (dưới ngưỡng, còn important, CI bắt buộc đỏ, không mergeable, còn review request bắt buộc) | Nên sửa trước khi merge |
| Còn blocker, hoặc test bắt buộc fail | Chưa nên merge |

## Vòng sửa

`fix` / `full`: kiểm chứng → sửa nhỏ nhất → test phần vừa sửa → parent đọc lại diff sửa → chấm lại một lần.

Không vòng thứ ba. Vẫn kẹt cổng → dừng, đưa finding còn lại, hỏi. Không nới test, không tắt hook, không xoá assertion cho xanh.

Sửa không được đụng `protected_paths`. Diff chạm path đó → finding, không sửa tiếp trong những path đó.

## Review

Không lệnh ghi. Không comment trừ khi chat nói comment sau khi đã xem điểm — khi đó vẫn là một việc riêng, không tự nâng mode thành `full`.

## Check fail

Sửa failure do PR gây ra, chỉ trong `fix` / `full`. Failure có trên base: báo baseline, không trừ, không "sửa giúp" trừ khi chat yêu cầu.

Không yếu CI, không đổi config check để né lỗi.

## Sync

Bắt buộc `--target`. Không có → hỏi một lần, không chọn nhánh. Conflict → dừng. Không force-push. Các bước ở SKILL.md mục 8.
