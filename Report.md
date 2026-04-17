# Part 1: Localhost vs Production

## Exercise 1.1: Phát hiện anti-patterns trong `app.py`

### Mục tiêu

Đọc file `app.py` trong thư mục `01-localhost-vs-production/develop` và tìm các vấn đề khiến ứng dụng **chạy được ở local nhưng chưa sẵn sàng cho production**.

---

## Các vấn đề tìm được trong `app.py`

### 1. Hardcode API key trong source code

```python
OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"
```

* API key được ghi trực tiếp trong file code.
* Đây là cách làm nguy hiểm vì nếu push code lên GitHub thì key có thể bị lộ.
* Trong production, secret nên được lưu bằng **environment variables** hoặc secret manager.

### 2. Hardcode database URL trong source code

```python
DATABASE_URL = "postgresql://admin:password123@localhost:5432/mydb"
```

* Thông tin kết nối database đang bị ghi cứng trong code.
* Điều này làm lộ username, password và gây rủi ro bảo mật.
* Ngoài ra còn làm app khó deploy sang môi trường khác vì không linh hoạt.

### 3. Không có config management

```python
DEBUG = True
MAX_TOKENS = 500
```

* Các config như `DEBUG`, `MAX_TOKENS`, port, host đều để cứng trong code.
* Khi chuyển từ local sang production sẽ khó thay đổi cấu hình.
* Cách đúng là đọc config từ file `.env` hoặc environment variables.

### 4. Dùng `print()` thay vì logging chuẩn

```python
print(f"[DEBUG] Got question: {question}")
print(f"[DEBUG] Response: {response}")
```

* Ứng dụng dùng `print()` để ghi log.
* Cách này không phù hợp cho production vì khó quản lý, khó filter, khó gửi sang hệ thống monitoring.
* Production nên dùng thư viện logging chuẩn, tốt hơn nữa là structured logging dạng JSON.

### 5. Log lộ secret ra màn hình

```python
print(f"[DEBUG] Using key: {OPENAI_API_KEY}")
```

* API key bị in thẳng ra log.
* Đây là lỗi bảo mật nghiêm trọng vì log có thể bị đọc bởi người khác hoặc lưu trên hệ thống ngoài ý muốn.
* Secret tuyệt đối không nên xuất hiện trong log.

### 6. Không có health check endpoint

* File không có endpoint như `/health` hoặc `/ready`.
* Nếu ứng dụng bị treo hoặc lỗi, hệ thống deploy sẽ không biết để restart hay ngừng gửi traffic.
* Trong production, health check là rất quan trọng để đảm bảo reliability.

### 7. Port bị hardcode cố định

```python
port=8000
```

* Ứng dụng luôn chạy ở port 8000.
* Trên cloud như Railway, Render hoặc Docker, port thường được cấp qua environment variable.
* Hardcode port làm app khó deploy và kém linh hoạt.

### 8. Host chỉ bind vào `localhost`

```python
host="localhost"
```

* Ứng dụng chỉ nghe request từ local machine.
* Điều này phù hợp khi chạy trên máy cá nhân, nhưng không phù hợp khi deploy container hoặc cloud.
* Trong production thường dùng `0.0.0.0` để app nhận traffic từ bên ngoài container.

### 9. Bật `reload=True`

```python
reload=True
```

* Chế độ reload tự động chỉ phù hợp cho development.
* Trong production, bật reload làm tăng overhead và không an toàn.
* Production nên chạy ở chế độ ổn định, không reload tự động.

### 10. Chạy trực tiếp bằng `if __name__ == "__main__"` theo kiểu local

```python
if __name__ == "__main__":
    uvicorn.run(...)
```

* Cách này thuận tiện cho local nhưng chưa tối ưu cho production.
* Trong production, app thường được chạy bằng process manager hoặc container command rõ ràng hơn.
* Điều này giúp kiểm soát lifecycle, logging, restart và deployment tốt hơn.

---

## Kết luận

File `app.py` có nhiều anti-pattern phổ biến của một ứng dụng chỉ phù hợp chạy ở local:

* hardcode secrets
* hardcode database URL
* thiếu config management
* logging không an toàn
* không có health check
* cấu hình host và port không phù hợp production
* bật debug/reload kiểu development

Vì vậy, ứng dụng này **có thể chạy trên máy cá nhân nhưng chưa production-ready**.

---

## Exercise 1.2: Chạy basic version

### Các bước thực hiện

```bash
pip install -r requirements.txt
python app.py
```

### Kết quả quan sát

* Ứng dụng chạy thành công trên local.
* Truy cập được endpoint `/`.
* Mở được Swagger UI tại `/docs`.
* Có thể test API bằng trình duyệt hoặc terminal.

### Nhận xét

* App **chạy được**, nhưng mới chỉ phù hợp cho môi trường development.
* Chưa đảm bảo các yêu cầu về bảo mật, reliability và khả năng deploy production.

---

## Exercise 1.3: So sánh basic version và advanced version

| Feature      | Basic                     | Advanced                     | Tại sao quan trọng?                         |
| ------------ | ------------------------- | ---------------------------- | ------------------------------------------- |
| Config       | Hardcode trong code       | Dùng environment variables   | Giúp linh hoạt khi đổi môi trường           |
| Secrets      | Viết trực tiếp trong code | Lấy từ env/secret manager    | Tránh lộ API key và password                |
| Logging      | `print()`                 | Logging chuẩn / JSON logging | Dễ theo dõi và giám sát                     |
| Health check | Không có                  | Có `/health`, `/ready`       | Giúp hệ thống biết app còn sống và sẵn sàng |
| Port/Host    | Hardcode `localhost:8000` | Đọc từ env, bind `0.0.0.0`   | Phù hợp cloud và container                  |
| Reload/Debug | `reload=True`             | Tắt trong production         | Ổn định và an toàn hơn                      |
| Shutdown     | Không rõ ràng             | Graceful shutdown            | Tránh mất request khi app bị dừng           |

---

## Checkpoint Part 1

* [x] Hiểu vì sao hardcode secrets là nguy hiểm
* [x] Biết environment variables quan trọng như thế nào
* [x] Hiểu vai trò của health check endpoint
* [x] Nhận ra sự khác nhau giữa developme
# Exercise 2.3

## Stage 1 làm gì?
Stage 1 là builder stage. Nó dùng để cài dependencies và các build tools cần thiết như `gcc`, `libpq-dev`. Stage này chỉ phục vụ cho quá trình build, không phải image cuối để deploy.

## Stage 2 làm gì?
Stage 2 là runtime stage. Nó tạo image cuối chỉ chứa những thành phần cần để chạy ứng dụng, bao gồm Python runtime, packages đã cài, source code và lệnh chạy app.

## Tại sao image nhỏ hơn?
Image nhỏ hơn vì stage runtime không chứa các build tools, apt cache và file trung gian từ stage builder. Nó chỉ copy phần cần thiết để chạy app, nên nhẹ hơn, sạch hơn và phù hợp production hơn.

## Exercise 2.3: Multi-stage build

### Stage 1 làm gì?
Stage 1 là **builder stage**. Nó dùng để:
- cài dependencies từ `requirements.txt`
- cài các build tools như `gcc`, `libpq-dev`
- chuẩn bị môi trường để build các package cần compile

Stage này **không phải image cuối để deploy**.

### Stage 2 làm gì?
Stage 2 là **runtime stage**. Nó dùng để:
- tạo image cuối để chạy ứng dụng
- copy các package đã cài từ stage 1 sang
- copy source code cần thiết
- tạo non-root user để tăng bảo mật
- cấu hình health check và lệnh start app

Đây là **image cuối dùng để chạy production**.

### Tại sao image nhỏ hơn?
Image nhỏ hơn vì stage runtime **không chứa**:
- build tools như `gcc`
- system libraries chỉ cần cho lúc build
- apt cache
- file trung gian của quá trình build

Nó chỉ giữ lại những gì cần để **chạy app**, nên:
- nhẹ hơn
- sạch hơn
- an toàn hơn
- phù hợp production hơn
- `gcc` là trình biên dịch C/C++, cần để build một số package Python có native extension.
- `libpq-dev` là thư viện development của PostgreSQL, thường cần khi cài package kết nối PostgreSQL như `psycopg2`.
- `apt cache` là dữ liệu tạm và danh sách package do `apt` tạo ra trong quá trình cài đặt; thường được xóa để giảm kích thước Docker image.