# Day 12 Lab – Deploy Your AI Agent to Production

**Student Name:** Nguyen Ngoc Tan
**Student ID:** 2A202600190
**Date:** 17/4/2026
**Course:** AICB-P1 · VinUniversity 2026

---

## Mục Tiêu

Sau khi hoàn thành lab này, tôi đã:

- Hiểu sự khác biệt giữa development và production.
- Containerize AI agent với Docker (multi-stage build).
- Deploy agent lên cloud platform (Railway).
- Bảo mật API với authentication, rate limiting và cost guard.
- Thiết kế hệ thống stateless, scalable và reliable.

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns phát hiện trong `app.py` (develop)

1. **Hardcode secrets** – API key, `DATABASE_URL` nhúng trực tiếp trong source.
2. **Không có config management** – không đọc giá trị từ environment variables.
3. **Logging sai cách** – dùng `print()` và log cả secret ra stdout.
4. **Không có health check endpoint** – platform không biết app còn sống hay không.
5. **Hardcode host + port** – cố định `0.0.0.0:8000`, không linh hoạt khi deploy.
6. **Debug mode bật mặc định** – lộ stack trace ra bên ngoài.
7. **Không xử lý shutdown** – bị kill đột ngột, mất request đang xử lý.

### Exercise 1.2: Chạy basic version

```bash
cd 01-localhost-vs-production/develop
pip install -r requirements.txt
python app.py

curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

→ App chạy được, nhưng chưa sẵn sàng cho production (thiếu health check, config, logging chuẩn).

### Exercise 1.3: So sánh develop vs production

| Feature      | Development (Basic)   | Production (Advanced) | Tại sao quan trọng                                    |
| ------------ | --------------------- | --------------------- | ----------------------------------------------------- |
| Config       | Hardcoded             | Env variables (.env)  | Tránh lộ secret, dễ cấu hình nhiều môi trường         |
| Health check | ❌ Không có            | ✅ `/health`, `/ready` | Platform tự restart/kiểm tra khi app lỗi              |
| Logging      | `print()`             | Structured JSON       | Dễ debug, tích hợp monitoring (Grafana, ELK, Loki)    |
| Shutdown     | Đột ngột (force stop) | Graceful shutdown     | Không mất request đang xử lý, đóng connection an toàn |
| Secrets      | Hardcode trong code   | Inject qua env vars   | Đáp ứng 12-Factor, tránh leak khi push code           |

### Checkpoint 1

- [x] Hiểu tại sao hardcode secrets là nguy hiểm.
- [x] Biết cách dùng environment variables (`pydantic-settings`, `.env`).
- [x] Hiểu vai trò của health check endpoint.
- [x] Biết graceful shutdown là gì và tại sao cần có.

---

## Part 2: Docker Containerization

### Exercise 2.1: Dockerfile – các câu hỏi cơ bản

1. **Base image:** image nền chứa OS + runtime (ví dụ `python:3.11-slim`) để build container. Quyết định kích thước, dependencies hệ thống và mức độ bảo mật.
2. **Working directory (`WORKDIR`):** thư mục mặc định trong container, nơi `COPY`, `RUN`, `CMD` được thực thi (ví dụ `/app`).
3. **Tại sao COPY `requirements.txt` trước:** tận dụng Docker layer cache. Khi chỉ sửa code mà không đổi dependencies, Docker sẽ reuse layer `pip install`, build nhanh hơn rất nhiều.
4. **CMD vs ENTRYPOINT:**
   - `CMD`: lệnh mặc định, có thể override khi `docker run`.
   - `ENTRYPOINT`: lệnh cố định, `CMD` khi đó sẽ trở thành argument cho `ENTRYPOINT`.

### Exercise 2.2: Build và run develop image

```bash
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .
docker run -p 8000:8000 my-agent:develop

curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```

### Exercise 2.3: Multi-stage build – so sánh kích thước

Multi-stage build tách phần build (cài dependencies, compile) khỏi phần runtime, chỉ copy artifact cần thiết sang image cuối → image gọn hơn và ít attack surface.

| Môi trường  | Kích thước image |
| ----------- | ---------------- |
| Development | ~1,660 MB        |
| Production  | ~236 MB          |
| Giảm        | **~85.8%**       |

### Exercise 2.4: Docker Compose stack

```bash
docker compose up
curl http://localhost/health
curl http://localhost/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain microservices"}'
```

Các service chính:

- `agent` – FastAPI service.
- `redis` – lưu state (history, rate limit, cost guard).
- `nginx` – reverse proxy / load balancer.

Các service communicate qua Docker network nội bộ (service name làm hostname, ví dụ `redis:6379`).

### Checkpoint 2

- [x] Hiểu cấu trúc Dockerfile (base image, layers, CMD).
- [x] Biết lợi ích của multi-stage build.
- [x] Hiểu Docker Compose orchestration.
- [x] Biết cách debug container với `docker logs`, `docker exec -it`.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Deploy lên Railway

- **Platform:** Railway (free $5 credit).
- **Public URL:** https://agent-production-1-production.up.railway.app
- **Env vars đã set:** `PORT`, `AGENT_API_KEY`, `REDIS_URL`, `LOG_LEVEL`.
- **Screenshot:**

![Railway deployment](./screenshot/image.png)

Các bước đã làm:

```bash
npm i -g @railway/cli
railway login
railway init
railway variables set PORT=8000
railway variables set AGENT_API_KEY=my-secret-key
railway up
railway domain
```

### Exercise 3.2: So sánh `render.yaml` vs `railway.toml`

| Khía cạnh         | `railway.toml`                   | `render.yaml`                                   |
| ----------------- | -------------------------------- | ----------------------------------------------- |
| Format            | TOML                             | YAML                                            |
| Service model     | Khai báo deploy/builder tối giản | Blueprint mô tả nhiều service (web, worker, db) |
| Env vars          | Qua CLI/dashboard                | Có thể khai báo trực tiếp trong file            |
| Health check path | Cấu hình ngắn gọn                | Hỗ trợ `healthCheckPath` rõ ràng                |
| Scaling           | CLI hoặc dashboard               | `numInstances`, `plan` ngay trong YAML          |

### Exercise 3.3 (Optional): GCP Cloud Run

Đã đọc `cloudbuild.yaml` và `service.yaml`: pipeline build image bằng Cloud Build → push lên Artifact Registry → deploy lên Cloud Run với autoscale theo concurrency.

### Checkpoint 3

- [x] Deploy thành công lên Railway.
- [x] Có public URL hoạt động.
- [x] Biết cách set environment variables trên cloud.
- [x] Biết xem logs qua `railway logs` / dashboard.

---

## Part 4: API Security

### Exercise 4.1: API Key Authentication

**Không có key:**

```bash
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

Response:

```json
{
  "detail": "Missing API key. Include header: X-API-Key: <your-key>"
}
```

**Sai key:**

```bash
curl http://localhost:8000/ask -X POST \
  -H "X-API-Key: wrong-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

Response:

```json
{
  "detail": "Invalid API key."
}
```

**Rotate key:** thay giá trị biến môi trường `AGENT_API_KEY` và redeploy — không sửa code, không commit secret.

### Exercise 4.2: JWT Authentication

**Lấy token:**

```bash
curl http://localhost:8000/token -X POST \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secret"}'
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in_minutes": 60,
  "hint": "Include in header: Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
}
```

**Dùng token:**

```bash
TOKEN="<token_ở_bước_trên>"
curl http://localhost:8000/ask -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain JWT"}'
```

Response:

```json
{
  "question": "Explain JWT",
  "answer": "Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.",
  "usage": {
    "requests_remaining": 99,
    "budget_remaining_usd": 0.000016
  }
}
```

Flow ngắn gọn: `username/password` → server cấp JWT (HS256, `exp = now + 60m`) → client gửi `Authorization: Bearer <token>` → server verify chữ ký + expiry → lấy `user_id` từ payload.

### Exercise 4.3: Rate Limiting

- **Thuật toán:** Sliding window dựa trên Redis sorted set.
- **Giới hạn:** 100 request / 60 giây / user (configurable qua `RATE_LIMIT_PER_MINUTE`).
- **Admin bypass:** user có role `admin` sẽ skip `check_rate_limit`.

Khi vượt limit:

```json
{
  "detail": {
    "error": "Rate limit exceeded",
    "limit": 100,
    "window_seconds": 60,
    "retry_after_seconds": 32
  }
}
```

### Exercise 4.4: Cost Guard

Thiết kế Cost Guard để kiểm soát chi phí LLM theo từng user và toàn hệ thống:

1. **Global budget:** nếu tổng chi vượt ngân sách tháng → trả `503 Service Unavailable`, tạm dừng nhận request.
2. **Per-user budget:** mỗi user giới hạn `$10/tháng`; vượt thì trả `402 Payment Required`.
3. **Warning:** khi user còn < 10% budget thì ghi log cảnh báo để admin theo dõi.

Tracking trong Redis theo key `budget:{user_id}:{YYYY-MM}`, TTL 32 ngày để auto-reset đầu tháng:

```python
def check_budget(user_id: str, estimated_cost: float) -> bool:
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    current = float(r.get(key) or 0)
    if current + estimated_cost > settings.MONTHLY_BUDGET_USD:
        return False
    r.incrbyfloat(key, estimated_cost)
    r.expire(key, 32 * 24 * 3600)
    return True
```

### Checkpoint 4

- [x] Implement API key authentication.
- [x] Hiểu và áp dụng JWT flow.
- [x] Implement rate limiting với Redis.
- [x] Implement cost guard với Redis + TTL theo tháng.

---

## Part 5: Scaling & Reliability

### Exercise 5.1: Health & Readiness Checks

- `/health` – **liveness probe**: chỉ kiểm tra tiến trình còn chạy, luôn trả `{"status": "ok"}`.
- `/ready` – **readiness probe**: kiểm tra các dependency (Redis ping, DB `SELECT 1`). OK → `200 {"status": "ready"}`, lỗi → `503 {"status": "not ready"}`.

Khi test: tắt Redis → `/health` vẫn pass, `/ready` fail → load balancer tự loại instance đó khỏi pool.

### Exercise 5.2: Graceful Shutdown

Các bước xử lý khi nhận `SIGTERM` từ orchestrator:

1. Đăng ký `signal.signal(signal.SIGTERM, shutdown_handler)`.
2. Set flag để app **ngừng nhận request mới**.
3. **Chờ các request đang xử lý hoàn thành** (có timeout để tránh treo).
4. Đóng kết nối Redis, DB, HTTP client pool.
5. `sys.exit(0)` để thoát an toàn.

Test: gửi request dài → `kill -TERM <pid>` → request vẫn hoàn thành trước khi process exit.

### Exercise 5.3: Stateless Design

Refactor khỏi anti-pattern lưu state trong memory:

- **Trước:** `conversation_history: dict[user_id, list]` trong RAM của từng instance → scale ngang sẽ mất state.
- **Sau:** lưu toàn bộ history vào Redis với key `history:{user_id}` (list, có TTL) → instance nào cũng đọc được cùng dữ liệu.

Lợi ích:

- Scale ngang thoải mái, không sticky session.
- Restart/deploy không mất data.
- Dễ share state giữa các service khác (analytics, admin dashboard…).

### Exercise 5.4: Load Balancing với Nginx

```bash
docker compose up --scale agent=3
```

Quan sát:

- 3 instance `agent` được tạo.
- Nginx phân phối request theo **round-robin**.
- Kill 1 instance → Nginx tự route sang 2 instance còn lại (health check upstream) → **high availability**.

Gửi 10 request liên tiếp và xem log:

```bash
for i in {1..10}; do
  curl http://localhost/ask -X POST \
    -H "Content-Type: application/json" \
    -d '{"question": "Request '$i'"}'
done
docker compose logs agent
```

Log xác nhận request được phân phối trên cả 3 instance.

### Exercise 5.5: Test Stateless

Script `test_stateless.py`:

1. Tạo conversation cho `user1`.
2. `docker kill` ngẫu nhiên 1 instance `agent`.
3. Gọi tiếp API với cùng `user_id` → conversation history vẫn còn nhờ Redis.

Kết quả: không mất state, hệ thống phục vụ bình thường ⇒ stateless design đạt yêu cầu.

### Checkpoint 5

- [x] Implement health & readiness checks.
- [x] Implement graceful shutdown cho SIGTERM.
- [x] Refactor thành stateless (state trong Redis).
- [x] Hiểu load balancing với Nginx.
- [x] Pass test stateless.

---

## Part 6: Final Project – Production-Ready AI Agent

### 6.1. Architecture

```
        ┌─────────────┐
        │   Client    │
        └──────┬──────┘
               │
               ▼
        ┌─────────────┐
        │ Nginx (LB)  │
        └──────┬──────┘
          ┌────┼────┐
          ▼    ▼    ▼
       Agent1 Agent2 Agent3   (FastAPI, stateless)
          └────┼────┘
               ▼
          ┌─────────┐
          │  Redis  │  (history + rate limit + cost guard)
          └─────────┘
```

### 6.2. Cấu trúc repository (`06-lab-complete/`)

```
06-lab-complete/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, endpoints /health /ready /ask /token
│   ├── config.py            # Pydantic settings từ env
│   ├── auth.py              # API key + JWT
│   ├── rate_limiter.py      # Sliding window trên Redis
│   ├── cost_guard.py        # Budget guard per-user + global
│   └── redis_store.py       # Redis client, history helpers
├── utils/
│   └── mock_llm.py          # Mock LLM (tránh tốn tiền OpenAI)
├── Dockerfile               # Multi-stage build (~236 MB)
├── docker-compose.yml       # agent (scale=3) + redis + nginx
├── nginx.conf               # Reverse proxy + round-robin
├── requirements.txt
├── .env.example
├── .dockerignore
├── railway.toml             # hoặc render.yaml
├── check_production_ready.py
└── README.md
```

### 6.3. Checklist sản phẩm

**Functional:**

- [x] Agent trả lời qua REST API (`/ask`).
- [x] Hỗ trợ conversation history theo user.
- [ ] Streaming responses (optional – chưa làm).

**Non-functional:**

- [x] Dockerized với multi-stage build (< 500 MB).
- [x] Config 100% từ environment variables, không hardcode secret.
- [x] API key authentication (+ JWT cho advanced flow).
- [x] Rate limiting 10 req/min/user (cấu hình được).
- [x] Cost guard $10/tháng/user + global budget.
- [x] Health check (`/health`) và readiness check (`/ready`).
- [x] Graceful shutdown với SIGTERM handler.
- [x] Stateless design (state lưu trong Redis).
- [x] Structured JSON logging.
- [x] Deploy lên Railway, public URL hoạt động.

### 6.4. Validation script

```bash
cd 06-lab-complete
python check_production_ready.py
```

Tất cả kiểm tra pass:

- [x] Dockerfile exists & valid, có multi-stage build.
- [x] `.dockerignore` tồn tại.
- [x] `/health` trả 200; `/ready` trả 200 khi dependency OK.
- [x] Thiếu API key → 401; sai → 401.
- [x] Vượt rate limit → 429 với `retry_after_seconds`.
- [x] Vượt budget → 402.
- [x] SIGTERM được handle (graceful shutdown).
- [x] Không còn state trong memory; tất cả qua Redis.
- [x] Logs ở dạng JSON.

### 6.5. Self-grading (theo rubric của lab)

| Criteria       | Points | Điểm tự đánh giá | Ghi chú                                            |
| -------------- | ------ | ---------------- | -------------------------------------------------- |
| Functionality  | 20     | 20               | `/ask` + history hoạt động                         |
| Docker         | 15     | 15               | Multi-stage, image ~236 MB                         |
| Security       | 20     | 20               | API key + JWT + rate limit + cost guard            |
| Reliability    | 20     | 19               | Health/ready + graceful shutdown (thiếu streaming) |
| Scalability    | 15     | 15               | Stateless + Nginx LB + scale=3                     |
| Deployment     | 10     | 10               | Railway public URL live                            |
| **Tổng**       | 100    | **99**           |                                                    |

---

## Những gì đã học

- **12-Factor App:** config qua env, logs qua stdout, stateless processes.
- **Docker & multi-stage build:** giảm image từ 1.6 GB xuống ~236 MB.
- **Cloud deployment:** sự khác biệt giữa Railway / Render / Cloud Run.
- **API security:** API key, JWT, rate limiting (sliding window), cost guard.
- **Reliability patterns:** health vs readiness, graceful shutdown, stateless design, load balancing.

## Next Steps

1. Thêm Prometheus + Grafana cho monitoring.
2. GitHub Actions CI/CD auto-deploy lên Railway.
3. Khám phá Kubernetes để scale lớn hơn.
4. OpenTelemetry cho distributed tracing.
5. Spot instances + auto-scaling để tối ưu chi phí.

---

## Submission

**GitHub repository:**

```
https://github.com/ngoctan1234/Lab12_NguyenNgocTan.git
```

**Public deployment:**

```
https://agent-production-1-production.up.railway.app
```

**Deadline:** 17/4/2026
