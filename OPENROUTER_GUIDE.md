# Hướng dẫn sử dụng OpenRouter làm Provider cho Code-Graph-RAG

## Tổng quan

OpenRouter là một API gateway cho phép bạn truy cập nhiều mô hình AI từ các nhà cung cấp khác nhau (OpenAI, Anthropic, Google, v.v.) qua một endpoint duy nhất. Code-Graph-RAG hỗ trợ sử dụng OpenRouter thông qua cấu hình endpoint tùy chỉnh của OpenAI-compatible API.

## Ưu điểm khi sử dụng OpenRouter

- **Đa dạng mô hình:** Truy cập hàng trăm mô hình qua một API key
- **Giá cạnh tranh:** So sánh và chọn provider rẻ nhất cho từng model
- **Dễ dàng chuyển đổi:** Không cần thay đổi code khi đổi model hay provider
- **Fallback tự động:** OpenRouter tự động chuyển sang provider khác nếu một provider gặp lỗi
- **Single API Key:** Quản lý nhiều provider chỉ với một key

## Các bước cài đặt

### Bước 1: Đăng ký OpenRouter

1. Truy cập https://openrouter.ai/
2. Đăng ký tài khoản mới
3. Xác nhận email đăng ký

### Bước 2: Lấy API Key

1. Đăng nhập vào OpenRouter
2. Vào trang **API Keys** ở menu Settings
3. Tạo mới API key bằng cách click nút **New Key**
4. Copy API key (định dạng: `sk-or-v1-...`)
5. Lưu key này để cấu hình trong file `.env`

### Bước 3: Top up số dư (nếu cần)

1. Vào trang **Billing**
2. Chọn phương thức thanh toán (Credit Card, Crypto, v.v.)
3. Nạp số tiền tối thiểu (thường là $5)
4. Đợi số tiền hiển thị trong account balance

## Cấu hình Code-Graph-RAG với OpenRouter

### Cách 1: Cấu hình cơ bản (CLI)

Đợi CSS 러시아
TẠO file `.env` trong thư mục root của code-graph-rag:

```bash
# .env file

# ========================================
# OPENROUTER CONFIGURATION
# ========================================

# Orchestrator Model - dùng cho các tác vụ chính
ORCHESTRATOR_PROVIDER=openai
ORCHESTRATOR_MODEL=anthropic/claude-3.5-sonnet
ORCHESTRATOR_API_KEY=sk-or-v1-YOUR_OPENROUTER_API_KEY
ORCHESTRATOR_ENDPOINT=https://openrouter.ai/api/v1

# Cypher Model - dùng để tạo câu lệnh Cypher query
CYPHER_PROVIDER=openai
CYPHER_MODEL=openai/gpt-4o-mini
CYPHER_API_KEY=sk-or-v1-YOUR_OPENROUTER_API_KEY
CYPHER_ENDPOINT=https://openrouter.ai/api/v1

# ========================================
# MEMGRAPH CONFIGURATION
# ========================================
MEMGRAPH_HOST=localhost
MEMGRAPH_PORT=7687
MEMGRAPH_HTTP_PORT=7444
LAB_PORT=3000
MEMGRAPH_BATCH_SIZE=1000

# ========================================
# DEFAULT SETTINGS
# ========================================
TARGET_REPO_PATH=.
```

### Cách 2: Mixed Providers (OpenRouter + các provider khác)

Bạn có thể kết hợp OpenRouter với các provider khác:

```bash
# .env file

# Orchestrator dùng OpenRouter (cho tác vụ nặng)
ORCHESTRATOR_PROVIDER=openai
ORCHESTRATOR_MODEL=anthropic/claude-3.5-sonnet
ORCHESTRATOR_API_KEY=sk-or-v1-YOUR_OPENROUTER_API_KEY
ORCHESTRATOR_ENDPOINT=https://openrouter.ai/api/v1

# Cypher dùng Ollama local (cho tốc độ và tiết kiệm)
CYPHER_PROVIDER=ollama
CYPHER_MODEL=codellama
CYPHER_ENDPOINT=http://localhost:11434/v1
```

### Cách 3: Bỏ qua .env, dùng CLI args trực tiếp

Run CLI với các thông số inline:

```bash
# Orchestrator và Cypher đều dùng OpenRouter
cgr start --repo-path /path/to/repo \
  --orchestrator openai:anthropic/claude-3.5-sonnet \
  --orchestrator-endpoint https://openrouter.ai/api/v1 \
  --orchestrator-api-key sk-or-v1-YOUR_OPENROUTER_API_KEY \
  --cypher openai:openai/gpt-4o-mini \
  --cypher-endpoint https://openrouter.ai/api/v1 \
  --cypher-api-key sk-or-v1-YOUR_OPENROUTER_API_KEY
```

## Các mô hình phổ biến trên OpenRouter

### Mô hình cho Orchestrator (chất lượng cao)

| Model | Provider | Đặc điểm | Giá |
|-------|----------|----------|-----|
| `anthropic/claude-3.5-sonnet` | Anthropic | Mạnh nhất cho reasoning, coding | $0.03/1M in, $0.15/1M out |
| `openai/gpt-4o` | OpenAI | Tốt cho đa nhiệm, billing tiện | $0.05/1M in, $0.15/1M out |
| `google/gemini-2.5-pro` | Google | Tốt cho long context (1M+ tokens) | $0.015/1M in, $0.06/1M out |

### Mô hình cho Cypher (nhanh, rẻ)

| Model | Provider | Đặc điểm | Giá |
|-------|----------|----------|-----|
| `openai/gpt-4o-mini` | OpenAI | Nhanh, rẻ, đủ cho query generation | $0.15/1M in, $0.60/1M out |
| `meta-llama/llama-3.2-1b-instruct` | Meta | Miễn phí (tiết kiệm chi phí) | $0 |
| `gryphe/mythomax-l2-13b` | Gryphe | Open source, nhanh | Rất rẻ |

## Ví dụ sử dụng thực tế

### Ví dụ 1: Query codebase với OpenRouter

```bash
# Cấu hình .env đã có sẵn
cgr start --repo-path ~/my-project
```

Trong CLI:
```
Your question: Show me all classes that implement IRepository
[Claude-3.5-Sonnet reasoning...]

Found 3 classes implementing IRepository:
1. SqlRepository in src/data/sql_repository.py
2. MongoRepository in src/data/mongo_repository.py
3. InMemoryRepository in src/test/test_repository.py
```

### Ví dụ 2: Optimization với model rẻ hơn

```bash
# Dùng Claude-3.5 cho orchestration, Llama-3.2 cho cypher
ORCHESTRATOR_PROVIDER=openai
ORCHESTRATOR_MODEL=anthropic/claude-3.5-sonnet
ORCHESTRATOR_API_KEY=sk-or-v1-YOUR_KEY
ORCHESTRATOR_ENDPOINT=https://openrouter.ai/api/v1

CYPHER_PROVIDER=openai
CYPHER_MODEL=meta-llama/llama-3.2-1b-instruct
CYPHER_API_KEY=sk-or-v1-YOUR_KEY
CYPHER_ENDPOINT=https://openrouter.ai/api/v1

cgr optimize python --repo-path ~/my-project
```

### Ví dụ 3: MCP Server với OpenRouter

```bash
claude mcp add --transport stdio code-graph-rag \
  --env TARGET_REPO_PATH=/absolute/path/to/project \
  --env CYPHER_PROVIDER=openai \
  --env CYPHER_MODEL=openai/gpt-4o-mini \
  --env CYPHER_API_KEY=sk-or-v1-YOUR_OPENROUTER_API_KEY \
  --env CYPHER_ENDPOINT=https://openrouter.ai/api/v1 \
  -- uv run --directory /path/to/code-graph-rag code-graph-rag mcp-server
```

## Lưu ý về Model ID format

**Quan trọng:** Khi dùng OpenRouter, model ID PHẢI theo format:

```
provider_name/model_name
```

**Không được dùng:**
```
# SAI
ORCHESTRATOR_MODEL=claude-3.5-sonnet
CYPHER_MODEL=gpt-4o-mini
```

**Phải dùng:**
```
# ĐÚNG
ORCHESTRATOR_MODEL=anthropic/claude-3.5-sonnet
CYPHER_MODEL=openai/gpt-4o-mini
```

### Danh sách model format phổ biến:

| Display Name | OpenRouter ID |
|--------------|---------------|
| Claude 3.5 Sonnet | `anthropic/claude-3.5-sonnet` |
| GPT-4o | `openai/gpt-4o` |
| GPT-4o-mini | `openai/gpt-4o-mini` |
| Gemini 2.5 Pro | `google/gemini-2.5-pro` |
| Llama 3.2 1B | `meta-llama/llama-3.2-1b-instruct` |
| Llama 3.3 70B | `meta-llama/llama-3.3-70b-instruct` |

Xem full list: https://openrouter.ai/models

## Troubleshooting

### Lỗi 1: "Invalid API key"

```
Error: 401 Unauthorized - Invalid API key
```

**Sửa:**
- Kiểm tra lại API key có đúng format `sk-or-v1-...`
- Đảm bảo API key chưa bị revoke
- Reset key và tạo mới nếu cần

### Lỗi 2: "Model not found"

```
Error: Model 'gpt-4o-mini' not found
```

**Sửa:**
- Dùng format đầy đủ: `openai/gpt-4o-mini`
- Kiểm tra danh sách model trên OpenRouter: https://openrouter.ai/models
- Một số model có thể không còn hỗ trợ

### Lỗi 3: "Insufficient credit"

```
Error: Payment required - Insufficient funds
```

**Sửa:**
- Nạp thêm tiền vào OpenRouter
- Switch sang model miễn phí (Llama 3.2)

### Lỗi 4: "Rate limit exceeded"

```
Error: 429 Too Many Requests
```

**Sửa:**
- Giảm số lượng request
- Dùng model rẻ hơn để giảm chi phí
- Tăng timeout trong config (nếu có option)

### Lỗi 5: "Endpoint connection failed"

```
Error: Failed to connect to https://openrouter.ai/api/v1
```

**Sửa:**
- Kiểm tra kết nối internet
- Đảm bảo không có firewall block
- Ping thử: `curl https://openrouter.ai/models`

## Tối ưu hóa chi phí

### Strategy 1: Orchestrator chính, Cypher rẻ

```bash
# Orchestrator: Claude-3.5 (chất lượng cao)
# Cypher: Llama-3.2 1B (miễn phí)
ORCHESTRATOR_MODEL=anthropic/claude-3.5-sonnet
CYPHER_MODEL=meta-llama/llama-3.2-1b-instruct
```

**Lợi ích:** Giảm ~90% chi phí cho Cypher queries, giữ chất lượng cao cho orchestration.

### Strategy 2: Dùng GPT-4o-mini cho mọi thứ

```bash
ORCHESTRATOR_MODEL=openai/gpt-4o-mini
CYPHER_MODEL=openai/gpt-4o-mini
```

**Lợi ích:** Cân bằng tốt về giá/hiệu năng, billing tiện từ OpenAI balance.

### Strategy 3: Hoàn toàn miễn phí

```bash
# Dùng Llama 3.2 cho cả 2
ORCHESTRATOR_MODEL=meta-llama/llama-3.2-1b-instruct
CYPHER_MODEL=meta-llama/llama-3.2-1b-instruct
```

**Lưu ý:** Chất lượng sẽ thấp hơn, chỉ nên dùng cho testing hoặc codebase nhỏ.

## Monitoring Usage

Kiểm tra usage trên OpenRouter dashboard:

1. Đăng nhập vào OpenRouter
2. Vào trang **Usage**
3. Xem chi tiết:
   - Số tokens đã dùng
   - Chi phí theo model
   - Requests per minute RPM
   - Errors rate

### Ví dụ script track usage:

```bash
# Check current balance
curl -H "Authorization: Bearer sk-or-v1-YOUR_KEY" \
  https://openrouter.ai/api/v1/credits

# Get usage stats (trong ngày)
curl -H "Authorization: Bearer sk-or-v1-YOUR_KEY" \
  https://openrouter.ai/api/v1/usage?start_date=2026-02-13
```

## Tài liệu tham khảo

- OpenRouter Docs: https://openrouter.ai/docs
- OpenRouter Models: https://openrouter.ai/models
- OpenRouter Pricing: https://openrouter.ai/models?price=pricing
- Code-Graph-RAG README: https://github.com/vitali87/code-graph-rag

## Câu hỏi thường gặp (FAQ)

**Q1: OpenRouter có miễn phí không?**
A: Có một số model miễn phí (Llama 3.2), nhưng các model thương mại cần top-up.

**Q2: Tôi có thể dùng cùng API key cho nhiều project không?**
A: Có, API key có thể dùng cho nhiều project và được billing chung.

**Q3: OpenRouter có hỗ trợ streaming không?**
A: Có, Code-Graph-RAG tự động sử dụng streaming nếu model hỗ trợ.

**Q4: Có cách nào test trước khi dùng không?**
A: Có, dùng `cgr doctor` để kiểm tra cấu hình trước khi chạy chính thức.

**Q5: OpenRouter có an toàn không?**
A: Có, OpenRouter tuân thủ GDPR, SOC 2, và không lưu trữ data sau khi xử lý.

---

**Lưu ý cuối:** Luôn đảm bảo API key và thông tin nhạy cảm được bảo mật. KHÔNG bao giờ commit file `.env` vào Git repository.

---

*Được cập nhật lần cuối: 2026-02-13*
