# Báo Cáo Vai Trò Cá Nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| :--- | :--- |
| **Họ và tên** | Nguyễn Huy Cương |
| **MSSV** | 2A202602842 |
| **Khóa / Lớp** | K4 - L3B (K4-L3B-DAY10) |
| **Tên nhóm** | Nhóm Không Biết / AlphaTeam |
| **Vai trò chính** | Trưởng nhóm / Data Ingestion, Corruption & Pipeline Integration Engineer |
| **Repository** | `K4-L3B-DAY10-KhongBiet-Data-Pipeline-Data-Observability` |
| **Ngày hoàn thành** | 2026-09-26 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu chính (Ownership)

| Module / Deliverable | File / Hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :---: |
| **Raw Data Ingestion & Preservation** | `src/ingestion/crossref.py`<br>- `parse_crossref_payload()`<br>- `fetch_source_records()`<br>- `load_raw_records()` | Crossref REST API JSON payload (hoặc local fallback snapshot) | `data/raw/crossref_response.json`<br>`data/raw/crossref_records.json` (24 PaperRecords) | **Hoàn thành** |
| **Data Cleaning & Pre-embedding Modeling** | `src/ingestion/cleaning.py`<br>- `build_clean_dataframe()` | Danh sách `PaperRecord` từ raw records | `data/clean/papers_clean.csv`<br>`data/clean/papers_clean.json` (24 dòng sạch, text_for_embedding chuẩn hóa) | **Hoàn thành** |
| **Data Corruption Suite** | `src/ingestion/corruption.py`<br>- `corrupt_clean_dataframe()` | DataFrame sạch `papers_clean.json` | 6 kịch bản lỗi, `data/results/corruption_log.json`, `papers_clean_corrupted.csv/json` | **Hoàn thành** |
| **Baseline Pipeline Orchestration** | `src/pipelines/phase1.py`<br>`script/run_phase1.py` | Settings & cấu hình luồng dữ liệu | `data/results/baseline_metrics.json`<br>`data/reports/phase1_report.md` | **Hoàn thành** |
| **Quản trị Môi trường & Git** | `core/config.py`, `.env`, Git repository | Thiết lập `.venv`, dependencies | Chạy 100% không lỗi trên môi trường ảo, quản lý Git branch | **Hoàn thành** |

### Việc hỗ trợ ngoài phạm vi chính (Cross-functional Support)
- **Hỗ trợ Observability & Self-healing:** Phối hợp cùng thành viên Trần Văn Khánh kết nối hàm `repair_from_raw_snapshot()` và kiểm tra chốt kiểm định Great Expectations 1.x trong `src/pipelines/corruption_flow.py`.
- **Quản lý tài liệu dự án:** Cập nhật bảng phân công nhóm `docs/TEAM.md` và chủ trì hoàn thiện báo cáo nhóm `report/group_report.md`.

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File / Hàm / Artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| **Ingestion API & Raw Preservation** | `src/ingestion/crossref.py` | Đã tải và bóc tách thành công 24 bản ghi học thuật, bảo toàn raw response JSON làm Lineage Anchor. | `python -c "from core.config import load_settings; from ingestion.crossref import fetch_source_records; s=load_settings(); r=fetch_source_records(s); print(f'Tín hiệu hoàn thành: Đã tải {len(r)} bài báo')"` (Output: 24 bài báo) |
| **Làm sạch & Ghép text embedding** | `src/ingestion/cleaning.py` | Lọc sạch thẻ HTML/XML rác, tính `age_days`, tạo cột `text_for_embedding` cấu trúc 5 phần, khử trùng lặp theo `paper_id`. | `python -c "from datetime import datetime, timezone; from core.config import load_settings; from ingestion.crossref import load_raw_records; from ingestion.cleaning import build_clean_dataframe; s=load_settings(); df=build_clean_dataframe(load_raw_records(s.paths.raw_records_json), datetime.now(timezone.utc)); print(f'Tín hiệu hoàn thành: Clean thành công {len(df)} dòng')"` (Output: 24 dòng) |
| **Tiêm lỗi thực nghiệm (Corruption)** | `src/ingestion/corruption.py` | Tiêm đủ 6 dạng lỗi thực tế: drop latest, blank summary, inject noise, truncate title, stale date, duplicate rows. | Đã xuất `data/results/corruption_log.json` ghi nhận chi tiết từng dòng bị tác động. |
| **Chạy toàn tuyến Phase 1** | `script/run_phase1.py` | Chạy end-to-end 6 bước, sinh ChromaDB baseline, đánh giá RAG Hit Rate đạt 100.0%, xuất báo cáo Phase 1. | `python script/run_phase1.py` (Exit code 0, tạo `data/reports/phase1_report.md`) |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### 4.1. Vấn đề cần giải quyết
1. **Bảo toàn dữ liệu gốc (Raw Preservation):** Khi gọi API ngoài, các lỗi mạng hoặc giới hạn tần suất (Rate Limit 429) có thể làm đứt gãy luồng xử lý. Cần có cơ chế Fallback offline đọc từ file snapshot cục bộ `data/raw/crossref_response.json` để pipeline luôn hoạt động thông suốt.
2. **Chuẩn hóa dữ liệu cho RAG Embedding:** Dữ liệu thô từ Crossref lẫn nhiều thẻ XML rác (`<jats:p>`), khoảng trắng bất thường và định dạng ngày tháng không đồng nhất. Cần xây dựng trường ngữ cảnh giàu thông tin `text_for_embedding` kết hợp Tiêu đề, Tác giả, Ngày xuất bản, Chuyên ngành và Tóm tắt để Vector Store tìm kiếm tối ưu.
3. **Mô phỏng sự cố thực tế (Synthetic Corruption):** Trong môi trường sản xuất, dữ liệu thường bị bẩn một cách âm thầm (mất dòng, lỗi mã hóa font, dữ liệu quá hạn, trùng lặp). Cần một bộ tiêm lỗi có kiểm soát để kiểm thử khả năng chịu lỗi và phát hiện của Quality Gate.

### 4.2. Cách triển khai
- **Cơ chế Fallback & Lineage Anchor:** Trong `fetch_source_records()`, nếu `refresh_source=True` thì mới gọi API, nếu gặp sự cố mạng hoặc `refresh_source=False` hệ thống sẽ đọc từ `data/raw/crossref_response.json`. Cả bản raw JSON nguyên bản và bản record đã parse đều được lưu độc lập để phục vụ Data Lineage.
- **Quy trình làm sạch dữ liệu Idempotent:** Trong `build_clean_dataframe()`:
  - Dùng regex `re.sub(r"<[^>]+>", " ", text)` để bóc tách toàn bộ tag HTML/XML rác.
  - Chuyển đổi ngày tháng theo chuẩn ISO, tính tuổi thọ bài báo: `age_days = (run_date - published).days`.
  - Định dạng chuỗi `text_for_embedding` đồng nhất cho ChromaDB.
  - Sử dụng `drop_duplicates(subset=["paper_id"], keep="first")` loại bỏ mọi trùng lặp khóa chính.
- **Tiêm 6 kịch bản lỗi:** Trong `corrupt_clean_dataframe()`:
  - Cắt bỏ 20% bài báo mới nhất (Drop latest).
  - Xóa rỗng `summary` ở 2 bài báo đầu tiên.
  - Chèn chuỗi ký tự rác vào bài báo thứ 3.
  - Cắt ngắn tiêu đề xuống dưới 8 ký tự ở bài báo thứ 4.
  - Lùi ngày xuất bản về quá khứ 365 ngày ở bài báo thứ 5.
  - Nhân bản dòng bản ghi để tạo vi phạm duplicate.
  - Đồng bộ tái tạo lại `text_for_embedding` và ghi nhật ký vào `corruption_log.json`.

### 4.3. Contract đầu vào, đầu ra
| Thành phần | Mô tả |
| :--- | :--- |
| **Input Ingestion** | Payload JSON từ Crossref REST API chứa các work items |
| **Output Ingestion** | Danh sách 24 đối tượng `PaperRecord` |
| **Input Cleaning** | Danh sách `PaperRecord` + `run_date: datetime` |
| **Output Cleaning** | `pd.DataFrame` 24 dòng sạch với các cột: `paper_id`, `title`, `summary`, `authors_joined`, `categories_joined`, `published`, `age_days`, `text_for_embedding` |
| **Điều kiện lỗi xử lý** | API trả về 429 Too Many Requests -> tự động kích hoạt Offline Fallback snapshot |

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi thiết kế cơ chế Ingestion cho pipeline, cần quyết định cách thức lưu trữ và khôi phục khi API bên ngoài bị lỗi hoặc vượt hạn mức (Rate Limit 429).
- **Các phương án đã cân nhắc:**
  1. *Phương án 1:* Mỗi lần chạy pipeline đều bắt buộc gọi REST API ngoài, nếu lỗi mạng thì pipeline dừng và báo Exception.
  2. *Phương án 2:* Triển khai kiến trúc **Raw Preservation & Fallback Anchor**: luôn duy trì một bản snapshot nguyên vẹn tại `data/raw/crossref_response.json`. Nếu cờ `REFRESH_SOURCE=1` mới gọi API ngoài; nếu không có mạng hoặc gặp lỗi API thì tự động nạp từ snapshot thô có sẵn.
- **Phương án đã chọn:** Chọn **Phương án 2**.
- **Lý do lựa chọn:** Đảm bảo tính khả lặp (Reproducibility), tính Idempotent của pipeline, bảo vệ hệ thống không bị phụ thuộc vào trạng thái mạng bên ngoài trong các bài kiểm thử tự động (CI/CD) và hỗ trợ hoàn hảo cho luồng phục hồi dữ liệu (Self-healing).
- **Bằng chứng:** Toàn bộ quá trình chạy thử nghiệm Phase 1 và Phase 2 đều thành công 100% với 24 bản ghi chuẩn hóa, không phụ thuộc vào trạng thái mạng bên ngoài.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng / Lỗi nguyên văn:**
  ```text
  ModuleNotFoundError: No module named 'great_expectations.expectations.metrics.column_aggregate_metrics.column_distinct_values_missing_from_column'
  UnicodeEncodeError: 'charmap' codec can't encode characters in position ...: character maps to <undefined>
  ```
- **Nguyên nhân gốc:**
  1. Thư mục dự án nằm sâu trong cấu trúc thư mục của Windows (`C:\Users\cuong\OneDrive\Documents\PHÁT TRIỂN BẢN THÂN\PROJECT__CODE\...`), khiến đường dẫn đến các module của thư viện `great_expectations` trong `.venv` vượt quá giới hạn 260 ký tự của Windows API (`MAX_PATH = 260`), dẫn tới lỗi `FileNotFoundError` ngầm khi import.
  2. Console Windows PowerShell mặc định sử dụng bảng mã `cp1252`, không in được các ký tự tiếng Việt có dấu trong câu lệnh `print()`.
- **Cách xử lý:**
  1. Di chuyển môi trường ảo `.venv` sang thư mục ngắn `C:\Users\cuong\.venv_day10` và tạo Directory Junction (Symlink Windows) trỏ về `.venv`, giúp rút ngắn độ dài đường dẫn từ 264 ký tự xuống còn 154 ký tự.
  2. Thêm cấu hình `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` tại đầu các script thực thi và chuẩn hóa chuỗi log trên console.
- **Cách xác minh sau khi sửa:**
  - Lệnh `.venv\Scripts\python.exe -c "import chromadb, great_expectations, sentence_transformers; print('Moi truong san sang')"` chạy thành công mã thoát 0.
  - Script toàn tuyến `python script/run_phase1.py` chạy mượt mà không gặp bất kỳ lỗi import hay encoding nào.

---

## 7. Hiểu biết về luồng End-to-End

1. **Dữ liệu đi từ Crossref đến Vector Index như thế nào?**
   - Dữ liệu thô từ API Crossref được bóc tách thành các đối tượng `PaperRecord`, sau đó qua bước cleaning để lọc sạch rác XML, chuẩn hóa ngày tháng và tính tuổi thọ bài báo (`age_days`). Dữ liệu được cấu trúc thành đoạn văn bản ngữ cảnh `text_for_embedding` gồm 5 trường thông tin quan trọng. Mô hình `sentence-transformers/all-MiniLM-L6-v2` chuyển đổi văn bản thành vector nhúng và lưu vào cơ sở dữ liệu vector ChromaDB cục bộ.
2. **Evaluation Set và Ground-Truth Document IDs dùng để đo retrieval/answer quality ra sao?**
   - Tập kiểm thử gồm 10 câu hỏi thuộc 4 dạng nghiệp vụ, mỗi câu hỏi đi kèm danh sách ID tài liệu gốc (`ground_truth_doc_ids`) và câu trả lời chuẩn (`ground_truth`). Khi RAG Agent truy vấn, hệ thống đo lường **Retrieval Hit Rate** (tài liệu được trả về có chứa đúng ID của tài liệu gốc hay không) và **Token F1 Score** (mức độ trùng khớp từ vựng giữa câu trả lời sinh ra và Ground Truth).
3. **Quality Checks khác Freshness Monitoring ở điểm nào trong bài lab?**
   - *Quality Checks* (qua Great Expectations 1.x) tập trung vào tính toàn vẹn cấu trúc dữ liệu: số lượng dòng, giá trị không được null, tính duy nhất của ID, độ dài tối thiểu của tóm tắt.
   - *Freshness Monitoring* tập trung vào tính kịp thời của dữ liệu theo thời gian thực (Freshness SLA): đo lường tỷ lệ các bài báo quá hạn (>180 ngày). Nếu tỷ lệ bài cũ vượt quá 25%, hệ thống sẽ kích hoạt cờ cảnh báo `is_fresh = False`.
4. **Vì sao phải dùng cùng một Test Set cho cả Baseline, Corrupted và Repaired?**
   - Để đảm bảo tính khách quan và khoa học (Controlled Experiment). Việc giữ cố định bộ câu hỏi kiểm thử và Ground Truth là điều kiện tiên quyết để so sánh công bằng sự sụt giảm hiệu năng khi dữ liệu bị lỗi và sự phục hồi sau khi dữ liệu được sửa chữa.
5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   - Repair thành công khi:
     - Quality Gate chuyển từ `False` trở lại `True` trên chốt kiểm định GX 1.x.
     - Số lượng bản ghi phục hồi đủ 24 dòng nguyên bản.
     - Metric Retrieval Hit Rate hồi phục từ mức sụt giảm (70.0%) trở lại 100.0%.
     - Bảng đối chiếu 3 trạng thái tại `data/reports/corruption_report.md` thể hiện rõ sự tương đương giữa trạng thái Repaired và Baseline.

---

## 8. Phân tích kết quả thực nghiệm

### Metrics chính đối chiếu 3 trạng thái

| Metric / Signal | Baseline (Sạch) | Corrupted (Bẩn) | Repaired (Phục hồi) | Nhận xét cá nhân |
| :--- | :---: | :---: | :---: | :--- |
| **Quality Gate (GX 1.x)** | **True** | **False** | **True** | Chốt kiểm soát phát hiện ngay dữ liệu vi phạm |
| **Tổng số bản ghi** | **24** | **22** | **24** | Khôi phục đầy đủ dữ liệu bị thất thoát |
| **Retrieval Hit Rate** | **100.0%** | **70.0%** | **100.0%** | Dữ liệu lỗi gây sụt giảm 30% khả năng truy hồi đúng tài liệu |
| **Mean Token F1** | **0.5154** | **0.2154** | **0.5154** | Mức độ trùng khớp từ vựng giảm hơn 58% khi dính dữ liệu rác |
| **Freshness SLA** | **True** (4.2% cũ) | **True** (8.3% cũ) | **True** (4.2% cũ) | Tỷ lệ bài cũ tăng khi tiêm lỗi stale date |

### Kết luận từ số liệu:
1. **Chuỗi nguyên nhân - kết quả khi tiêm lỗi:**  
   *Tiêm 6 dạng lỗi (xóa summary, cắt tiêu đề, nhân bản)* $\rightarrow$ *Quality Gate GX 1.x báo động `False`* $\rightarrow$ *Retrieval Hit Rate sụt giảm từ 100% xuống 70.0%, Token F1 rơi tự do từ 0.5154 xuống 0.2154 (Hiện tượng Silent Failure).*
2. **Chuỗi nguyên nhân - kết quả khi phục hồi:**  
   *Kích hoạt `repair_from_raw_snapshot()` từ Raw Preservation* $\rightarrow$ *Khôi phục 24 dòng sạch, Quality Gate GX 1.x đạt `True`* $\rightarrow$ *Retrieval Hit Rate và Token F1 phục hồi hoàn toàn về mức 100% và 0.5154.*

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất:
1. **Kiến trúc Data Lineage & Raw Preservation:** Giữ nguyên dữ liệu thô ban đầu là chìa khóa vàng giúp hệ thống có thể tự phục hồi (Self-healing) mà không phải chịu rủi ro phụ thuộc vào API bên ngoài.
2. **Data Observability chặn đứng Silent Failure:** Trong các hệ thống RAG/AI, lỗi dữ liệu thường không làm sập server mà làm mô hình trả lời sai một cách âm thầm. Việc đặt các chốt kiểm định tự động như Great Expectations là bắt buộc trước khi nạp dữ liệu vào Vector Database.
3. **Thiết kế Idempotent Pipeline:** Mọi hàm biến đổi dữ liệu cần có tính chất Idempotent — chạy lại nhiều lần với cùng đầu vào luôn cho cùng một kết quả chuẩn xác.

### Hướng cải thiện nếu có thêm thời gian:
- Tích hợp một giao diện Web trực quan (Interactive Observability Dashboard bằng Streamlit) hiển thị biểu đồ phân bố độ tuổi bài báo, trực quan hóa vector drift và tự động phát cảnh báo qua Webhook/Slack khi phát hiện vi phạm Freshness SLA.

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Người báo cáo:** Nguyễn Huy Cương  
**MSSV:** 2A202602842  
**Ngày xác nhận:** 2026-09-26  
