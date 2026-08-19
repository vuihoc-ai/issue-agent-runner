# Spec: issue-agent-runner (tsubame) - as-built

- **Project:** tsubame (repo công khai: `issue-agent-runner`)   **Status:** AS-BUILT
- **Date:** 2026-08-19   **Nguồn:** `issue_agent_runner/*.py`, `examples/`, README
- **Links:** design: ./design.md

## 1. Problem + intent

Các tích hợp "ticket → PR" do nhà cung cấp lớn vận hành đều tiện, nhưng chúng quyết định thay người
dùng ba thứ: dùng tracker nào, chạy trên đám mây nào, và dùng agent nào - kèm hoá đơn tính theo
token trong sandbox của họ.

tsubame là bản tham chiếu **tối giản, tự host được**: một đường đi duy nhất từ ticket tới draft PR,
đọc hết được trong một lần ngồi, và chỗ cắm agent là **một hàm**. Đây cũng là project công khai của
Marc (repo public + bài blog), nên tiêu chí "đọc hiểu được" quan trọng ngang tiêu chí "chạy được".

## 2. Scope

**IN:**
- Đọc work item từ tracker qua REST.
- Clone repo đích vào thư mục tạm.
- Gọi backend agent theo đúng một chữ ký hàm.
- Tạo nhánh, commit, mở **draft** PR bằng `git` + `gh`.
- Bình luận ngược lại ticket kèm link PR.
- Hai bản tham chiếu backend + một backend demo không tốn tiền.

**OUT / non-goals:**
- Không dịch vụ chạy thường trực.
- Không registry plugin, không cơ chế khám phá backend.
- Không ma trận nhiều nhà cung cấp.
- Không tự merge: luôn dừng ở draft PR.

## 3. User scenarios

### US-1 (P1): biến một ticket thành draft PR
- WHEN chạy `issue-agent-runner run KEY-1`, hệ thống PHẢI đọc ticket, chạy agent trên bản clone
  mới, mở draft PR và bình luận link về ticket.

### US-2 (P1): đổi agent mà không phải học kiến trúc
- WHEN muốn đổi agent, người dùng PHẢI chỉ cần sửa một hàm `run_agent(task, workdir)` (hoặc trỏ biến
  môi trường sang lệnh khác), không phải đăng ký plugin.

### US-3 (P1): chạy thử toàn tuyến mà không tốn tiền
- WHEN trỏ backend vào `echo_agent.sh`, hệ thống PHẢI chạy hết luồng ticket → PR với một thay đổi
  giữ chỗ, không gọi model nào.

### US-4 (P2): không để lại rác trên máy
- WHEN một lượt chạy kết thúc, thư mục làm việc PHẢI bị xoá.

## 4. Functional requirements

- **FR-001:** Hệ thống PHẢI đọc work item từ tracker qua REST bằng token do người dùng cấp.
- **FR-002:** Hệ thống PHẢI clone repo vào thư mục tạm dùng một lần.
- **FR-003:** Backend agent PHẢI là đúng một hàm `run_agent(task: str, workdir: str) -> None`.
- **FR-004:** Backend mặc định PHẢI là subprocess cấu hình bằng biến môi trường - trường hợp phổ
  biến không cần sửa code.
- **FR-005:** PR mở ra PHẢI ở trạng thái **draft**.
- **FR-006:** Hệ thống PHẢI bình luận trạng thái + link PR về ticket.
- **FR-007:** Thư mục làm việc PHẢI bị xoá sau khi chạy.
- **FR-008:** Cấu hình PHẢI qua tệp môi trường có ví dụ đi kèm, và tài liệu PHẢI khuyến nghị token
  quyền tối thiểu.

## 5. Success criteria

- **SC-001:** Một người lạ đọc hết đường đi chính trong một lần, không phải nhảy qua nhiều lớp trừu
  tượng.
- **SC-002:** Đổi agent = sửa một tệp.
- **SC-003:** Chạy được toàn tuyến với $0 và không cần agent thật.
- **SC-004:** Không có gì chạy thường trực; không có trạng thái nào sống ngoài một lượt chạy.

## 6. Key entities

| Entity | Nội dung |
|---|---|
| Work item | khoá ticket + mô tả lấy từ tracker |
| Task | mô tả công việc truyền cho agent |
| Workdir | bản clone tạm, xoá sau khi xong |

## 7. Assumptions

- `git` và `gh` có trên PATH và đã đăng nhập cho repo đích.
- Người dùng tự chịu trách nhiệm về agent mình cắm vào.

## 8. Ràng buộc

Đây là repo **công khai**: không được nhắc công ty, khách hàng hay hạ tầng nội bộ của Marc; ví dụ
phải trung lập (`owner/example-repo`, `KEY-1`).

## 9. Câu hỏi mở

- Có hỗ trợ thêm tracker khác ngoài bản REST hiện tại không - hiện cố ý giữ một đường duy nhất.
