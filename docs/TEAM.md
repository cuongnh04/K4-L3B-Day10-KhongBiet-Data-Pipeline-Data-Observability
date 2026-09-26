# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `[Điền tên nhóm]`
- **Mã Nhóm / Lớp:** `K4-L3-DAY10`
- **Tên Repository Nộp Bài:** `K4-L3-DAY10-TenNhom-DataPipeline`

---

## # Thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân | % Đóng góp |
|---:|---|---|---|---|---|:---:|
| 1 | Nguyễn Huy Cương | 2A202602842 | `cuongnh190204@gmail.com` | **Trưởng nhóm / Data Ingestion, Corruption & Pipeline Integration** (Bước 2, 3, 6, 7 & `core/`, `src/ingestion/`, `src/pipelines/phase1.py`) | `report/2A202602842_NguyenHuyCuong.md` | 50% |
| 2 | Trần Văn Khánh | 2A202602413 | `khanh.tv@...` | **Data Observability, RAG Retrieval & Evaluation / Recovery Specialist** (Bước 4, 5, 8 & `src/observability/`, `src/evaluation/`, `src/retrieval/`, `src/pipelines/corruption_flow.py`) | `report/2A202602413_TranVanKhanh.md` | 50% |

---

## # Chi tiết đóng góp cá nhân

### ## Nguyễn Huy Cương - 2A202602842
- **Vai trò:** Trưởng nhóm, Phụ trách Data Ingestion, Cleaning, Corruption & Pipeline Integration.
- **Công việc chi tiết phụ trách (theo `huongdan.md` & `CHECKPOINTS.md`):**
  - **Khởi tạo & Cấu hình:** Thiết lập môi trường `.venv`, dependencies (`pyproject.toml`/`requirements.txt`), quản lý biến môi trường `.env`.
  - **Bước 2 (CP0):** Thu thập dữ liệu API & Cất giữ bản gốc (`src/ingestion/crossref.py`). Hoàn thiện `parse_crossref_payload()` và `fetch_source_records()`, cơ chế fallback offline (`crossref_response.json`, `crossref_records.json`).
  - **Bước 3 (CP1):** Làm sạch & Chuẩn bị văn bản Embedding (`src/ingestion/cleaning.py`). Hoàn thiện `build_clean_dataframe()`, chuẩn hóa văn bản, tính `age_days`, tạo `text_for_embedding`, khử trùng lặp `paper_id`.
  - **Bước 6 (CP3):** Xây dựng và thực thi Baseline Pipeline Pha 1 (`src/pipelines/phase1.py`, `script/run_phase1.py`). Xuất báo cáo `data/reports/phase1_report.md` và kiểm chứng các artifact đầu ra.
  - **Bước 7 (CP4):** Tiêm lỗi dữ liệu thực nghiệm (`src/ingestion/corruption.py`). Hoàn thiện `corrupt_clean_dataframe()` với 6 dạng lỗi, lưu `corruption_log.json`.
  - **Bước 9:** Điều phối Git, rà soát bảo mật không leak API key, tổng hợp báo cáo nhóm `report/group_report.md` và hoàn thiện báo cáo cá nhân.
- **Điều học được / Đóng góp chính:**
  - Nắm vững kiến trúc Data Lineage Anchor, bảo toàn Raw Preservation, xử lý sự cố mạng với Fallback mechanism, và kỹ thuật tiêm lỗi (Data Corruption Injection) giả lập sự cố thực tế.

### ## Trần Văn Khánh - 2A202602413
- **Vai trò:** Kỹ sư Data Observability, RAG Retrieval & Benchmark Evaluation / Self-Healing.
- **Công việc chi tiết phụ trách (theo `huongdan.md` & `CHECKPOINTS.md`):**
  - **Bước 4 (CP1):** Thiết lập Chốt kiểm soát chất lượng với Great Expectations 1.x & Freshness SLA (`src/observability/quality.py`). Cấu hình Ephemeral Context, triển khai 4 Expectation bắt buộc và hàm `evaluate_freshness_sla()`.
  - **Bước 5 (CP2):** Xây dựng bộ đề đánh giá chuẩn Benchmark Test Set (`src/evaluation/testset.py`). Hoàn thiện hàm `build_test_set()` sinh 10 câu hỏi Ground Truth qua 4 nhóm nghiệp vụ (`summary`, `authors`, `date`, `categories`), lưu `data/eval/test_set.json`.
  - **RAG & Vector Database (CP2, CP3):** Quản lý embedding model `all-MiniLM-L6-v2`, ChromaDB collection indexing, đo lường retrieval Hit Rate và Token F1 score.
  - **Bước 8 (CP5):** Đo lường suy giảm hiệu năng (Silent Failure), thực thi cơ chế phục hồi dữ liệu an toàn `repair_from_raw_snapshot()` và đối chiếu 3 trạng thái (`src/pipelines/corruption_flow.py`, `script/run_corruption_flow.py`, `data/reports/corruption_report.md`).
  - **Bước 9 & Demo (CP6):** Chuẩn bị kịch bản và cùng trình diễn Live Demo (Checkpoint 6: bảng so sánh 3 trạng thái, giải thích cơ chế self-healing), rà soát nộp bài VLearn LMS và hoàn thiện báo cáo cá nhân.
- **Điều học được / Đóng góp chính:**
  - Thành thạo Great Expectations 1.x chuẩn mới, phương pháp giám sát Data Drift & Freshness SLA, cơ chế Idempotent Self-Healing bảo vệ hệ thống RAG khỏi lỗi Silent Failure.
