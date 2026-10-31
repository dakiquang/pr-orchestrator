# Cổng

Rule repo và check bắt buộc của repo thắng bảng này. Config `merge.min_score` thắng 8.0 nếu có.

## Merge

Chỉ `full`, và chỉ đúng PR chat đã gọi `full`, khi tất cả đúng:

1. Điểm ≥ `merge.min_score` (mặc định 8.0) sau trần.
2. Không còn blocker, không còn finding important về đúng đắn hoặc bảo mật do PR gây ra.
3. Test bắt buộc không fail. CI bắt buộc xanh nếu `merge.require_ci` là true. Mặc định `require_ci: false` — khi đó CI đỏ không tự chặn, nhưng phải ghi trạng thái thật, không ghi là xanh.
4. PR mở, mergeable, không conflict.
5. Không còn review request chưa giải mà repo coi là bắt buộc.
6. Chat không thu hẹp thành review-only sau khi đã gọi `full`.

Thiếu một điều → không merge. Không hạ cổng để merge cho xong.

`fix` không merge trừ khi chat cũng nói merge, hoặc mode là `full`.

## Trần điểm

Áp sau khi làm tròn 0.5. Trần thấp hơn thì lấy trần.

| Điều kiện | Trần |
|---|---:|
| 1 blocker do PR gây ra | 6.5 |
| ≥ 3 blocker do PR gây ra | 5.0 |
| Còn finding đúng đắn hoặc bảo mật mức important, do PR gây ra | 7.5 |
| Test bắt buộc fail vì PR | 7.5 và không merge |

Blocker có từ trước không kích trần. Ghi riêng.

Nit không kích trần, không chặn merge. Vẫn liệt kê.

Điểm ≥ 8.0 và không còn blocker / important mới đủ điều kiện merge. Trần 7.5 hoặc test fail thì không đủ, dù các hạng khác cao.

## Vòng sửa

`fix` / `full`: kiểm chứng → sửa nhỏ nhất → test phần vừa sửa → parent đọc lại diff sửa → chấm lại một lần.

Không vòng thứ ba. Vẫn kẹt cổng → dừng, đưa finding còn lại, hỏi. Không nới test, không tắt hook, không xoá assertion cho xanh.

Sửa không được đụng `protected_paths`. Diff chạm path đó → finding, không sửa tiếp trong những path đó.

## Review

Không lệnh ghi. Không comment trừ khi chat nói comment sau khi đã xem điểm — khi đó vẫn là một việc riêng, không tự nâng mode thành `full`.

Không merge khi test bắt buộc fail hoặc còn blocker, kể cả khi điểm bị làm tròn lên sát trần.

## Check fail

Sửa failure do PR gây ra, chỉ trong `fix` / `full`. Failure có trên base: báo baseline, không trừ, không "sửa giúp" trừ khi chat yêu cầu.

Không yếu CI, không đổi config check để né lỗi.

## Sync

Bắt buộc `--target`. Không có → hỏi một lần, không chọn nhánh. Conflict → dừng. Không force-push. Đưa commit bằng `git cherry-pick -x`.
