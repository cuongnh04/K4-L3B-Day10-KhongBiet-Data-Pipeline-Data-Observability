# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| :--- | :--- |
| **Khóa / Lớp** | K4 - L3B (K4-L3B-DAY10) |
| **Tên nhóm** | Nhóm Không Biết / AlphaTeam |
| **Repository** | `K4-L3B-DAY10-KhongBiet-Data-Pipeline-Data-Observability` |
| **Ngày hoàn thành** | 2026-09-26 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module / Deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | **Nguyễn Huy Cương** | 2A202602842 | Trưởng nhóm / Data Ingestion, Corruption & Pipeline Integration | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `src/ingestion/corruption.py`, `src/pipelines/phase1.py`, `script/run_phase1.py` |
| 2 | **Trần Văn Khánh** | 2A202602413 | Data Observability, RAG Retrieval & Self-Healing Specialist | `src/observability/quality.py`, `src/evaluation/testset.py`, `src/retrieval/`, `src/pipelines/corruption_flow.py`, `script/run_corruption_flow.py` |

---

## 2. Tóm tắt kết quả

Nhóm đã xây dựng hoàn chỉnh hệ thống Data Pipeline end-to-end cho mô hình RAG Agent học thuật, tích hợp chốt kiểm soát chất lượng dữ liệu (Data Observability Gate) theo chuẩn **Great Expectations 1.x** kết hợp giám sát độ tươi mới **Freshness SLA** (ngưỡng 180 ngày). 

Ở Pha 1 (Baseline Pipeline), hệ thống thu thập và làm sạch thành công 24 bản ghi từ Crossref API, lưu trữ an toàn các raw artifacts (`crossref_response.json`, `crossref_records.json`), đánh chỉ mục ChromaDB với mô hình `all-MiniLM-L6-v2` và đạt chỉ số Retrieval Hit Rate 100.0%, Token F1 0.5154 trên bộ benchmark testset 10 câu hỏi Ground Truth. Chốt kiểm định chất lượng đạt trạng thái `PASSED (True)`.

Ở Pha 2 (Corruption & Self-healing), nhóm đã tiêm thực nghiệm 6 kịch bản sự cố dữ liệu thực tế (bỏ rơi bài mới, xóa summary, chèn noise, cắt tiêu đề, ngày cũ, trùng lặp). Khi dữ liệu bị lỗi, Quality Gate lập tức báo động (`False`), và hệ thống AI xuất hiện hiện tượng **Silent Failure** nghiêm trọng: Retrieval Hit Rate sụt giảm từ 100.0% xuống 70.0% và Token F1 giảm hơn 58% (từ 0.5154 xuống 0.2154). Khi kích hoạt cơ chế phục hồi dữ liệu an toàn (`Idempotent Repair`) từ bản lưu trữ thô ban đầu, dữ liệu sạch được khôi phục 100%, Quality Gate đạt trở lại `True`, và Retrieval Hit Rate cùng Token F1 hồi phục hoàn toàn về mức ban đầu (100.0% và 0.5154).

Toàn bộ quy trình được kiểm chứng tự động qua các script `script/run_phase1.py` và `script/run_corruption_flow.py` chạy exit code 0.

---

## 3. Kiến trúc và luồng dữ liệu

### Luồng End-to-End

```text
[Crossref REST API] 
       │
       ▼ (Fallback offline snapshot)
[data/raw/crossref_response.json & records.json] (Raw Lineage Anchor)
       │
       ▼ (src/ingestion/cleaning.py)
[data/clean/papers_clean.csv & json] (24 clean records, text_for_embedding)
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
[Great Expectations 1.x & Freshness SLA]   [ChromaDB: papers-baseline]
       │                                 │
       ▼                                 ▼
[data/quality/baseline_quality_report]   [RAG Retrieval & Evaluation (10 Qs)]
                                         │
                                         ▼
                               [Baseline Metrics: 100% Hit Rate]
                                         │
       ┌─────────────────────────────────┘
       ▼
[Data Corruption Suite: 6 lỗi] ──► [Quality Gate: FAIL (False)]
                               ──► [ChromaDB: papers-corrupted]
                               ──► [Silent Failure: Hit Rate drops to 70%]
       │
       ▼ (Idempotent Repair from Raw Snapshot)
[Self-Healing Restoration]     ──► [Quality Gate: PASS (True)]
                               ──► [ChromaDB: papers-repaired]
                               ──► [Metrics Recovered: 100% Hit Rate]
                               ──► [data/reports/corruption_report.md]
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output / Artifact | Owner |
| :--- | :--- | :--- | :--- | :--- |
| **Ingestion** | Crossref REST API / Raw Snapshot | Gọi API, retry 429/503, fallback offline snapshot, parse payload | `data/raw/crossref_response.json`<br>`data/raw/crossref_records.json` | Nguyễn Huy Cương |
| **Cleaning** | Raw `PaperRecord` objects | Lọc XML rác, chuẩn hóa ngày tháng, tính `age_days`, tạo `text_for_embedding`, khử trùng `paper_id` | `data/clean/papers_clean.csv`<br>`data/clean/papers_clean.json` | Nguyễn Huy Cương |
| **Embedding / Index** | Clean / Corrupted / Repaired DataFrame | Sinh vector embedding `all-MiniLM-L6-v2`, nạp 3 collection ChromaDB | `data/chroma/`<br>`papers_embeddings*.json` | Trần Văn Khánh |
| **Evaluation** | Clean DataFrame & ChromaDB index | Sinh bộ test set 10 câu hỏi (4 dạng), đo Hit Rate & Token F1 | `data/eval/test_set.json`<br>`data/results/*_metrics.json` | Trần Văn Khánh |
| **Observability** | DataFrame ở các giai đoạn | Cấu hình GX 1.x Ephemeral Context (4 Expectations) + Freshness SLA | `data/quality/*_quality_report.json`<br>`freshness_report.json` | Trần Văn Khánh |
| **Corruption / Repair** | Clean DataFrame & Raw records | Tiêm 6 kịch bản lỗi, ghi nhật ký, phục hồi idempotent từ raw snapshot | `data/results/corruption_log.json`<br>`papers_clean_repaired.csv/json` | Cương & Khánh |
| **Orchestration** | Pipeline components | Điều phối toàn tuyến Phase 1 và Phase 2, xuất báo cáo đối chiếu markdown | `phase1_report.md`<br>`corruption_report.md` | Nguyễn Huy Cương |

---

## 4. Cách tái hiện kết quả

### Cấu hình không chứa Secret

| Biến / Cấu hình | Giá trị sử dụng |
| :--- | :--- |
| `LLM_PROVIDER` | `mock` (hoặc `gemini` khi có key) |
| `LLM_MODEL` | `mock-model` (hoặc `gemini-2.5-flash`) |
| `Embedding model` | `sentence-transformers/all-MiniLM-L6-v2` |
| `Số lượng Crossref records` | 24 bài báo |
| `Retrieval top_k` | 4 tài liệu |
| `Freshness threshold` | 180 ngày |

### Lệnh cài đặt môi trường

```bash
uv venv
uv sync
```

### Lệnh chạy thực nghiệm

1. **Chạy toàn tuyến Phase 1 (Baseline Pipeline):**
   ```bash
   python script/run_phase1.py
   ```
2. **Chạy toàn tuyến Phase 2 (Corruption Flow, Repair & 3-State Comparison):**
   ```bash
   python script/run_corruption_flow.py
   ```

### Kết quả tái hiện

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
| :--- | :--- | :--- | :--- |
| `python script/run_phase1.py` | **Thành công** (Exit code 0) | 2026-09-26 09:49:50 | `data/reports/phase1_report.md`, `baseline_metrics.json` |
| `python script/run_corruption_flow.py` | **Thành công** (Exit code 0) | 2026-09-26 09:50:50 | Bảng đối chiếu 3 cột, `data/reports/corruption_report.md` |

---

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu
- **Source:** Crossref REST API (`https://api.crossref.org/works`).
- **Query / Filter:** `agentic retrieval augmented generation large language model`, `from-pub-date:...,has-abstract:true`.
- **Số bản ghi nhận được:** 24 bản ghi.
- **Cơ chế Fallback:** Tự động nạp bản sao cục bộ `data/raw/crossref_response.json` khi mạng mất kết nối hoặc API trả về lỗi 429 Too Many Requests.

### Schema dữ liệu sạch

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| :--- | :--- | :---: | :--- | :--- |
| `paper_id` | `str` | Có | Định danh DOI duy nhất | Bỏ qua record nếu thiếu DOI |
| `title` | `str` | Có | Tiêu đề bài báo | Bỏ qua record nếu thiếu tiêu đề |
| `summary` | `str` | Có | Tóm tắt nội dung | Làm sạch thẻ `<jats:p>`, bóc tách XML rác |
| `authors_joined` | `str` | Có | Danh sách tác giả ghép nối | Ghép chuỗi bằng dấu phẩy |
| `categories_joined`| `str` | Có | Chuyên ngành nghiên cứu | Mặc định `"General"` nếu rỗng |
| `published` | `str` | Có | Ngày xuất bản chuẩn `YYYY-MM-DD` | Parse date-parts từ API |
| `age_days` | `int` | Có | Tuổi đời dữ liệu (tính đến ngày chạy) | Tính `(run_date - published).days` |
| `text_for_embedding`| `str` | Có | Đoạn văn bản hoàn chỉnh 5 phần | Định dạng theo cấu trúc tiêu chuẩn phục vụ Vector DB |

---

## 6. Evaluation Setup

| Thành phần | Cấu hình thực tế |
| :--- | :--- |
| **Số câu hỏi benchmark** | 10 câu hỏi Ground Truth |
| **Các dạng câu hỏi (`question_type`)** | 3 câu `summary`, 3 câu `authors`, 2 câu `date`, 2 câu `categories` |
| **Ground-truth document ID** | Mảng chứa chính xác DOI của tài liệu mục tiêu |
| **Embedding model** | `sentence-transformers/all-MiniLM-L6-v2` |
| **Vector store** | ChromaDB với 3 collection: `papers-baseline`, `papers-corrupted`, `papers-repaired` |
| **Top K retrieval** | 4 passages |
| **Tính cố định của Test Set** | Dùng chung 1 file `data/eval/test_set.json` cho cả 3 giai đoạn để đảm bảo tính khách quan của thực nghiệm |

---

## 7. Bảng so sánh 3 trạng thái: Baseline vs Corrupted vs Repaired

| Metric / Tiêu chí | Baseline (Sạch) | Corrupted (Bẩn) | Repaired (Phục hồi) | Tác động của Corruption | Mức độ phục hồi | Nhận xét chuyên môn |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Quality Gate (GX 1.x)** | **True** | **False** | **True** | Báo động đỏ vi phạm chất lượng | Khôi phục 100% | GX 1.x phát hiện chính xác lỗi schema |
| **Số bản ghi** | **24** | **22** | **24** | Thất thoát 2 bản ghi do drop/dup | Phục hồi đủ 24 dòng | Loại bỏ hoàn toàn bản ghi trùng lặp |
| **Retrieval Hit Rate** | **100.0%** | **70.0%** | **100.0%** | **Sụt giảm 30.0%** | **Hồi phục 100.0%** | Minh chứng hiện tượng Silent Failure |
| **Mean Token F1** | **0.5154** | **0.2154** | **0.5154** | **Sụt giảm 58.2%** | **Hồi phục 100.0%** | Câu trả lời bị giảm chất lượng nghiêm trọng |
| **Judge Accuracy** | **50.0%** | **30.0%** | **50.0%** | **Sụt giảm 20.0%** | **Hồi phục 100.0%** | Đánh giá tính chuẩn xác ngữ nghĩa |
| **Mean Judge Score** | **3.00 / 5.0** | **1.80 / 5.0** | **3.00 / 5.0** | **Sụt giảm 1.2 điểm** | **Hồi phục 100.0%** | Đánh giá tổng quát câu trả lời AI |
| **Freshness SLA** | **True** (4.2%) | **True** (8.3%) | **True** (4.2%) | Tỷ lệ bài cũ tăng gấp đôi | Trở lại mức chuẩn ban đầu | Vẫn nằm trong giới hạn cho phép |

### Hai kết luận có quan hệ nhân quả quan trọng:
1. **Dữ liệu bẩn dẫn tới suy giảm âm thầm (Silent Failure):**  
   Khi dữ liệu bị tiêm lỗi (xóa summary, cắt tiêu đề, làm cũ ngày), hệ thống không quăng lỗi Exception lúc chạy mà câu trả lời của AI bị suy giảm nghiêm trọng: Retrieval Hit Rate giảm từ **100% xuống 70%** và Token F1 rơi từ **0.5154 xuống 0.2154**. Nhờ có chốt kiểm định Great Expectations 1.x, sự cố này đã bị chặn đứng ngay trước khi dữ liệu được nạp vào serving layer.
2. **Cơ chế Idempotent Repair khôi phục hoàn hảo hiệu năng:**  
   Bằng việc kích hoạt `repair_from_raw_snapshot()` dựa trên bản lưu trữ thô nguyên vẹn (`crossref_records.json`), toàn bộ các chỉ số của RAG Agent đã được khôi phục nguyên vẹn về mức ban đầu (**Hit Rate 100.0%, Token F1 0.5154**), chứng minh tính khả thi của kiến trúc Self-healing Data Pipeline.

---

## 8. Checklist nghiệm thu bài nộp

- [x] Đầy đủ thông tin nhóm và thành viên, tỷ lệ đóng góp (50% - 50%).
- [x] Lệnh tái hiện chạy mượt mà không lỗi: `python script/run_phase1.py` và `python script/run_corruption_flow.py`.
- [x] Báo cáo cá nhân của Nguyễn Huy Cương đã được hoàn thiện tại `report/2A202602842_NguyenHuyCuong.md`.
- [x] File cấu hình an toàn `.env` không chứa secret hay API key thật, đã có `.env.example`.
- [x] Tất cả các artifacts (`baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json`, `corruption_log.json`, `phase1_report.md`, `corruption_report.md`) đã được sinh ra đầy đủ và kiểm chứng chính xác.
