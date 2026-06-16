# Potential Future AI Providers

Last updated: Jun 16, 2026

## Currently Implemented (5)

| Provider | Models | Free Tier |
|----------|--------|-----------|
| Groq | 8 | 30 RPM, 1K–14.4K req/day |
| Cerebras | 2 | 30 RPM, 1M tokens/day |
| SambaNova | 7 | Small developer quota |
| OpenRouter | 24 | 50 req/day free |
| Gemini | 7 | Varies by model/region |

---

## High Priority Candidates

### 1. Cloudflare Workers AI
- **Free tier:** 10K neurons/day, 300 RPM
- **Models:** 16 (Llama 3.3 70B, QwQ 32B, etc.)
- **API:** OpenAI-compatible at `https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1/chat/completions`
- **Auth:** `Authorization: Bearer <CLOUDFLARE_API_TOKEN>`
- **Env vars:** `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`
- **Phone required:** No
- **Notes:** No credit card needed. Generous RPM. Solid model catalog.

### 2. OVHcloud AI Endpoints
- **Free tier:** 2 req/min/IP sandbox, 400 RPM with key
- **Models:** 10 (GPT-OSS, Qwen3, Mistral)
- **API:** OpenAI-compatible at `https://endpoints.ai.cloud.ovh.net/v1/chat/completions`
- **Auth:** `Authorization: Bearer <OVH_AI_ENDPOINTS_ACCESS_TOKEN>`
- **Env vars:** `OVH_AI_ENDPOINTS_ACCESS_TOKEN`
- **Phone required:** No
- **Notes:** European provider. Sandbox works without key (2 req/min/IP).

### 3. Scaleway
- **Free tier:** 1M free tokens
- **Models:** 10
- **API:** OpenAI-compatible at `https://api.scaleway.ai/v1/chat/completions`
- **Auth:** `Authorization: Bearer <SCALEWAY_API_KEY>`
- **Env vars:** `SCALEWAY_API_KEY`
- **Phone required:** No
- **Notes:** European provider. Permanent free tier.

---

## Medium Priority Candidates

### 4. Cohere
- **Free tier:** 20 RPM, 1K req/month
- **Models:** 2 (Command R+, Aya Expanse 32B)
- **API:** Native Cohere SDK or v2 chat endpoint
- **Auth:** `Authorization: Bearer <COHERE_API_KEY>`
- **Env vars:** `COHERE_API_KEY`
- **Phone required:** No
- **Notes:** Small but reliable. Good for fallback. Different API format from OpenAI — needs adapter.

### 5. Routeway
- **Free tier:** Explicit `:free` zero-price models
- **Models:** 15
- **API:** OpenAI-compatible
- **Auth:** `Authorization: Bearer <ROUTEWAY_API_KEY>`
- **Env vars:** `ROUTEWAY_API_KEY`
- **Phone required:** No
- **Notes:** Use `:free` suffix for zero-price models.

### 6. Novita AI
- **Free tier:** Zero-price live chat models
- **Models:** 4
- **API:** OpenAI-compatible
- **Auth:** `Authorization: Bearer <NOVITA_API_KEY>`
- **Env vars:** `NOVITA_API_KEY`
- **Phone required:** No
- **Notes:** Small catalog but truly free.

### 7. DashScope (Alibaba)
- **Free tier:** 1M free tokens/model, 90 days
- **Models:** 11 (Qwen3 series)
- **API:** OpenAI-compatible at `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions`
- **Auth:** `Authorization: Bearer <DASHSCOPE_API_KEY>`
- **Env vars:** `DASHSCOPE_API_KEY`
- **Phone required:** No
- **Notes:** High quality Qwen3 models. Time-limited free tier (90 days).

---

## Low Priority / Smaller Tiers

### 8. LLM7
- **Free tier:** Shared free tier, optional free token
- **Models:** 4
- **API:** OpenAI-compatible
- **Env vars:** `LLM7_API_KEY` (optional)
- **Phone required:** No

### 9. ZAI
- **Free tier:** Free Flash models only
- **Models:** 2
- **API:** OpenAI-compatible
- **Env vars:** `ZAI_API_KEY`
- **Phone required:** No

### 10. Kilo
- **Free tier:** Free auto-router, no key needed
- **Models:** 1
- **API:** OpenAI-compatible
- **Env vars:** `KILO_API_KEY` (optional)
- **Phone required:** No

### 11. Ollama Cloud
- **Free tier:** Free cloud usage with session/weekly limits
- **Models:** 17
- **API:** OpenAI-compatible
- **Env vars:** `OLLAMA_API_KEY`
- **Phone required:** No

---

## Excluded (Phone Verification Required)

| Provider | Reason |
|----------|--------|
| NVIDIA NIM | Phone verification required |
| Mistral La Plateforme | Phone verification required |
| Codestral | Same as Mistral |

## Excluded (High Risk / Other)

| Provider | Reason |
|----------|--------|
| GitHub Models | Token leak risk — high punishment |
| iFlow | Shut down Apr 17, 2026 |
