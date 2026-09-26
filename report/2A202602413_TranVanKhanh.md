# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Trần Văn Khánh             |
| MSSV               | 2A202602413                     |
| Khóa/Lớp         | K4-L3B              |
| Tên nhóm         | KhongBiet     |
| Vai trò chính    | Data Observability, RAG Retrieval & Evaluation / Recovery Specialist                 |
| Repository         | https://github.com/cuongnh04/K4-L3B-Day10-KhongBiet-Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-09-26               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Data Observability & Freshness | `src/observability/quality.py` | `pd.DataFrame` sau khi clean | Report kiểm định GX và Freshness Report JSON | Hoàn thành |
| Benchmark Test Set | `src/evaluation/testset.py` | `pd.DataFrame` chứa dữ liệu bài báo | `test_set.json` chứa 10 câu hỏi đánh giá | Hoàn thành |
| Vector Indexing & RAG | `src/retrieval/index.py` | `pd.DataFrame` clean / corrupted / repaired | 3 ChromaDB collections, đo Hit Rate & F1 | Hoàn thành |
| Self-Healing & Corruption Flow | `src/pipelines/corruption_flow.py` | Dữ liệu baseline & corrupted data | File báo cáo so sánh `corruption_report.md`, các json log | Hoàn thành |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Cài đặt Great Expectations 1.x | `quality.py` | `baseline_quality_report.json`, `corrupted_quality_report.json` | Chạy lệnh test sinh ra json file có status pass/fail |
| Tiêu chuẩn hóa đánh giá (Benchmark) | `testset.py` | `test_set.json` (10 questions) | Kiểm tra trực tiếp file sinh ra đủ format và câu hỏi |
| Thực thi Self-Healing | `corruption_flow.py` | `corruption_report.md` | Chạy `python script/run_corruption_flow.py` |

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Phần của mình giải quyết 2 bài toán chính trong RAG Pipeline:
1. Phát hiện dữ liệu bẩn (Silent Failure): Đảm bảo các documents khi đưa vào Vector Store không bị khuyết tật (mất summary, title, bị trùng) hay quá cũ (vượt 180 ngày).
2. Cơ chế tự phục hồi (Idempotent Repair): Khi nhận thấy collection vector bị hỏng bởi dữ liệu rác, hệ thống phải tự động phục hồi về bản gốc đáng tin cậy mà không phá vỡ pipeline.

### Cách tiếp cận và giải pháp

- Sử dụng **Great Expectations 1.x** thông qua `ephemeral mode`, định nghĩa 4 laws thiết yếu để quét DataFrame ngay trước khi nạp ChromaDB.
- Tích hợp logic **Freshness SLA** để đo tuổi đời bài báo (`age_days > 180`), gán cờ `is_fresh` = False nếu tỷ lệ rác quá hạn > 25%.
- Quản lý quy trình `corruption_flow`: Khi lỗi xảy ra, tiến hành tái lập trạng thái từ snapshot raw `crossref_records.json` thành 1 bộ Collection `repaired` hoàn toàn độc lập, so sánh metric 3 pha để chứng minh sự phục hồi.
