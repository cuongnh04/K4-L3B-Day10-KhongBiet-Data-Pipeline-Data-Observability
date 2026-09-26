# Báo Cáo Đối Chiếu 3 Trạng Thái: Phân Tích Suy Giảm & Khôi Phục Dữ Liệu

> **Thời điểm xuất báo cáo:** 2026-09-26 02:50:46 UTC  
> **Mô hình Embedding:** `sentence-transformers/all-MiniLM-L6-v2`  
> **LLM Provider:** `mock` (`mock-model`)  

---

## 1. Bảng So Sánh Tổng Hợp 3 Trạng Thái (Benchmark Comparison)

| Chỉ số / Tiêu chí | Trạng thái 1: Baseline (Sạch) | Trạng thái 2: Corrupted (Bẩn) | Trạng thái 3: Repaired (Phục hồi) | Nhận xét thay đổi |
| :--- | :---: | :---: | :---: | :--- |
| **Data Quality Gate (GX 1.x)** | **`True`** | **`False`** | **`True`** | Quality Gate chặn đứng dữ liệu bẩn |
| **Số lượng bản ghi** | **24** dòng | **22** dòng | **24** dòng | Phục hồi nguyên trạng sau repair |
| **Retrieval Hit Rate** | **100.0%** | **70.0%** | **100.0%** | Hit Rate sụt giảm khi bẩn, phục hồi 100% |
| **Mean Token F1 Score** | **0.5154** | **0.2154** | **0.5154** | Khôi phục độ trùng khớp từ vựng |
| **Judge Accuracy** | **50.0%** | **20.0%** | **50.0%** | Ngăn chặn hiện tượng Silent Failure |
| **Mean Judge Score** | **3.00 / 5.0** | **1.80 / 5.0** | **3.00 / 5.0** | Điểm chất lượng câu trả lời hồi sinh |

---

## 2. Phân Tích Chi Tiết Sự Cố Dữ Liệu (Silent Failure Analysis)
- **Cơ chế tiêm lỗi (Corruption Suite):** Đã áp dụng 6 kịch bản lỗi thực tế (Drop latest records, Blank summary, Inject noise, Truncate title, Stale date, Duplicate rows).
- **Hành vi hệ thống khi bị lỗi (Silent Failure):**
  - Mặc dù hệ thống không gặp Exception hay crash code lúc runtime, việc truy vấn trả về ngữ cảnh sai lệch khiến câu trả lời của AI bị ảo giác (hallucination) hoặc trả về chuỗi rác.
  - Quality Gate theo chuẩn Great Expectations 1.x lập tức gắn cờ cảnh báo vi phạm schema và tính duy nhất.

---

## 3. Cơ Chế Tự Phục Hồi Dữ Liệu (Idempotent Repair Architecture)
- **Nguồn phục hồi:** Trích xuất từ `data/raw/crossref_records.json` (Lineage Anchor bất biến).
- **Tính Idempotent:** Quá trình phục hồi có thể thực thi nhiều lần độc lập mà kết quả đầu ra luôn đồng nhất, ghi đè toàn bộ vector bẩn trên ChromaDB collection `papers-repaired`.
- **Kết quả nghiệm thu:** Sau khi chạy Repair, toàn bộ các chỉ số Retrieval Hit Rate (100.0%) và Token F1 (0.5154) quay trở về tương đương trạng thái Baseline ban đầu.
