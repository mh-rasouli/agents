# Migration to OpenRouter + Gemini 3 Pro

This document explains the changes made to use OpenRouter API with Gemini 3 Pro instead of Claude API.

## What Changed

### 1. API Provider
- **Before**: Anthropic Claude API (direct)
- **After**: OpenRouter API (aggregator) using Gemini 3 Pro

### 2. Configuration

#### Environment Variables
```bash
# Before
ANTHROPIC_API_KEY=sk-ant-...
MODEL_NAME=claude-sonnet-4-5-20250929

# After
OPENROUTER_API_KEY=sk-or-v1-...
MODEL_NAME=google/gemini-pro-1.5
```

#### Settings File (`config/settings.py`)
- Renamed `ANTHROPIC_API_KEY` → `OPENROUTER_API_KEY`
- Changed default model to `google/gemini-pro-1.5`
- Increased `MAX_TOKENS` to 8192 (Gemini supports longer context)

### 3. Dependencies

#### requirements.txt
```diff
- anthropic>=0.39.0
+ openai>=1.12.0  # OpenRouter uses OpenAI-compatible API
```

### 4. LLM Client (`utils/llm_client.py`)

- **Class renamed**: `ClaudeClient` → `LLMClient`
- **API endpoint**: Uses OpenRouter base URL (`https://openrouter.ai/api/v1`)
- **Client library**: Uses `openai` package (OpenAI-compatible)
- **Backwards compatibility**: Added `claude_client = llm_client` alias

## Migration Steps

### For Users

1. **Get OpenRouter API Key**
   - Visit https://openrouter.ai/keys
   - Create account and generate API key
   - Note: OpenRouter charges per-token usage

2. **Update Environment Variables**
   ```bash
   # Copy new example
   cp .env.example .env

   # Edit .env and add your OpenRouter key
   OPENROUTER_API_KEY=sk-or-v1-your-key-here
   ```

3. **Install New Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run System**
   ```bash
   # Test with single brand
   python main.py --brand "دیجی‌کالا"

   # Batch mode
   python main.py --google-sheets
   ```

### For Developers

No code changes required if you were using the base agent classes. The `self.llm` reference in agents automatically uses the new LLM client.

If you were directly importing `claude_client`, it still works (alias), but consider updating to:
```python
from utils.llm_client import llm_client
```

## Available Models on OpenRouter

You can change the model in `.env`:

### Google Models
- `google/gemini-pro-1.5` (default)
- `google/gemini-2.0-flash-exp` (faster)
- `google/gemini-pro` (legacy)

### Other Models
OpenRouter supports 100+ models. See https://openrouter.ai/models

Examples:
- `anthropic/claude-3.5-sonnet` (if you want Claude back)
- `openai/gpt-4-turbo`
- `meta-llama/llama-3.1-70b-instruct`

## Cost Comparison

| Provider | Model | Cost (per 1M tokens) |
|----------|-------|---------------------|
| Anthropic (direct) | Claude Sonnet 4.5 | ~$3 input / $15 output |
| OpenRouter | Gemini Pro 1.5 | ~$1.25 input / $5 output |
| OpenRouter | GPT-4 Turbo | ~$10 input / $30 output |

**Note**: OpenRouter adds a small markup (~5-10%) for API aggregation.

## Benefits of OpenRouter

1. **Model Flexibility**: Switch between 100+ models without code changes
2. **Cost Optimization**: Choose cheaper models for different tasks
3. **Fallback**: Use multiple models as fallbacks
4. **Rate Limits**: Pooled across multiple providers

## Rollback

To rollback to Claude API:

1. **Revert dependencies**:
   ```bash
   pip install anthropic>=0.39.0
   pip uninstall openai
   ```

2. **Restore old files**:
   ```bash
   git checkout HEAD~1 -- config/settings.py utils/llm_client.py .env.example
   ```

3. **Update .env**:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-your-key
   MODEL_NAME=claude-sonnet-4-5-20250929
   ```

## Troubleshooting

### "OpenRouter API not available"
- Check that `OPENROUTER_API_KEY` is set in `.env`
- Verify key starts with `sk-or-v1-`
- Test key at https://openrouter.ai/

### "Invalid model name"
- Check model name format: `provider/model-name`
- List available models: https://openrouter.ai/models
- Ensure model is not deprecated

### "Rate limit exceeded"
- OpenRouter has rate limits per API key
- Consider using a paid plan
- Implement exponential backoff (already in code)

### "JSON parsing errors"
- Gemini may format JSON differently than Claude
- The client already handles markdown code blocks
- Check prompt engineering if persistent issues

## Performance Notes

**Gemini 3 Pro** compared to **Claude Sonnet 4.5**:
- ✅ Faster response times
- ✅ Lower cost
- ✅ Longer context window (2M tokens vs 200K)
- ⚠️ May require prompt tuning for optimal results
- ⚠️ Different "personality" in responses

## Support

- OpenRouter Docs: https://openrouter.ai/docs
- Gemini Docs: https://ai.google.dev/gemini-api/docs
- Issues: https://github.com/mh-rasouli/agents/issues
