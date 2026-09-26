# Báo Cáo Tuyến Dữ Liệu Cơ Sở (Baseline Pipeline Report - Phase 1)

> **Thời điểm xuất báo cáo:** 2026-09-26 02:49:50 UTC  
> **Nguồn dữ liệu:** Crossref REST API  
> **LLM Provider:** `mock` (Model: `mock-model`)  
> **Mô hình Embedding:** `sentence-transformers/all-MiniLM-L6-v2`  

---

## 1. Thu Thập & Làm Sạch Dữ Liệu (Ingestion & Cleaning)
- **Tổng số bản ghi sạch:** 24 dòng (khử trùng lặp theo `paper_id`).
- **File lưu trữ CSV:** `C:\Users\cuong\OneDrive\Documents\PHÁT TRIỂN BẢN THÂN\PROJECT__CODE\VINAI\K4-L3B-Day10-KhongBiet-Data-Pipeline-Data-Observability\data\clean\papers_clean.csv`
- **File lưu trữ JSON:** `C:\Users\cuong\OneDrive\Documents\PHÁT TRIỂN BẢN THÂN\PROJECT__CODE\VINAI\K4-L3B-Day10-KhongBiet-Data-Pipeline-Data-Observability\data\clean\papers_clean.json`
- **ChromaDB Collection:** `papers-baseline`

---

## 2. Chốt Kiểm Soát Chất Lượng Dữ Liệu (Great Expectations 1.x & Freshness SLA)
- **Trạng thái Quality Gate:** `PASSED (True)`
- **Great Expectations 1.x Validations:** `True`
- **Số bản ghi kiểm tra:** 24 dòng
- **Giám sát độ tươi mới (Freshness SLA):**
  - **Trạng thái Freshness:** `ĐẠT CHUẨN (True)`
  - **Ngưỡng SLA bài báo cũ:** 180 ngày
  - **Số bài quá hạn (>180 ngày):** 1 / 24 (4.2%)
  - **Bài mới nhất:** 2026-07-22
  - **Bài cũ nhất:** 2026-03-28

---

## 3. Chỉ Số Hiệu Năng RAG Nền (Baseline Benchmarks)
| Chỉ số đánh giá | Giá trị đạt được | Ghi chú |
| :--- | :---: | :--- |
| **Số lượng câu hỏi kiểm thử (Benchmark Test Set)** | **10** câu | Phân bổ 4 nhóm (summary, authors, date, categories) |
| **Retrieval Hit Rate** | **100.0%** | Tỷ lệ tìm đúng tài liệu chứa câu trả lời |
| **Mean Token F1 Score** | **0.5154** | Độ trùng khớp từ vựng giữa câu trả lời và Ground Truth |
| **Judge Accuracy** | **50.0%** | Đánh giá tính chính xác về mặt ngữ nghĩa |
| **Mean Judge Score** | **3.00 / 5.0** | Điểm trung bình chất lượng câu trả lời |

---

## 4. Kết Luận
Toàn tuyến Phase 1 đã thực thi thành công. Dữ liệu vượt qua chốt kiểm định Great Expectations 1.x và đảm bảo Freshness SLA. Vector index đã sẵn sàng phục vụ cho các thực nghiệm tiêm lỗi ở Phase 2.
