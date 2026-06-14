# Daily Tasks Manual — 2026-06-14


## Task 1
- **Project**: GAE
- **Date**: 2026-06-13
- **Title**: Chơi và tinh chỉnh đường cong độ khó cho Timeline 7 để tối ưu trải nghiệm người chơi, đảm bảo sự cân bằng giữa thử thách và tiến bộ
- **Description**:
1. Background: Timeline 7 hiện tại đã được triển khai trong game, nhưng cần được chơi thử và tinh chỉnh đường cong độ khó (difficulty curve) dựa trên phản hồi và dữ liệu thực tế để đảm bảo trải nghiệm người chơi mượt mà và hấp dẫn.
2. Objective: Thực hiện chơi thử toàn bộ các màn trong Timeline 7, ghi nhận các điểm mất cân bằng (quá khó hoặc quá dễ), sau đó tinh chỉnh các tham số như stats kẻ địch, số lượng quân, và modifier buff để tạo ra đường cong độ khó tối ưu.
3. Notes: Cần phối hợp với team QA và developer để cập nhật các config (ScriptableObject) và test lại sau mỗi lần tinh chỉnh.
- **Acceptance Criteria**:
1. Đã chơi và đánh giá ít nhất 3 lần toàn bộ các màn trong Timeline 7 để xác định điểm bất thường.
2. Đường cong độ khó đã được tinh chỉnh sao cho người chơi trung bình có thể vượt qua với tỷ lệ thành công 60-70%.
3. Các tham số tinh chỉnh đã được cập nhật trong EraDataSO và ContentDataSO tương ứng.
4. Không có lỗi gameplay hoặc crash trong quá trình chơi thử sau tinh chỉnh.
5. Tài liệu thay đổi đã được ghi nhận trong GDD và commit code.