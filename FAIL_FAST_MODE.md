# Fail Fast Mode - API Key Validation

## 🛑 Overview

The system now operates in **"Fail Fast"** mode for API key errors. Instead of falling back to low-quality rule-based processing, the system:

1. ✅ **Validates API key** before starting analysis
2. ❌ **Stops immediately** if API key is invalid
3. 💾 **Saves progress** for batch processing
4. 📢 **Shows clear error message** with resolution steps
5. 🔄 **Allows resume** after fixing the API key

---

## 🎯 Why Fail Fast?

### **Problems with Rule-Based Fallback:**
- ❌ Low-quality outputs (empty CSVs, generic insights)
- ❌ Wastes time processing with poor results
- ❌ User doesn't know API key is invalid until reviewing outputs
- ❌ Difficult to distinguish between LLM and rule-based outputs

### **Benefits of Fail Fast:**
- ✅ Immediate notification of API key issues
- ✅ No wasted processing time
- ✅ Clear error message with fix instructions
- ✅ Progress saved for resume
- ✅ Ensures consistent high-quality outputs

---

## 📋 How It Works

### **1. Single Brand Mode**

```bash
python main.py --brand "Dafi_Iran" --website "https://dafiiran.com/"
```

**Process:**
1. System validates API key with test call
2. If invalid → stops immediately with error
3. If valid → proceeds with analysis

**Example Output (Invalid Key):**

```
==================================================================
       Brand Intelligence Agent - Multi-Agent System
            Iranian Brand Analysis for Advertising
==================================================================

API Status: [OK] API key configured (sk-or-v1...)

Analyzing brand: Dafi_Iran
Website: https://dafiiran.com/
Starting brand intelligence analysis for: Dafi_Iran
Validating OpenRouter API key...

╔══════════════════════════════════════════════════════════════╗
║                     API KEY ERROR                            ║
╚══════════════════════════════════════════════════════════════╝

❌ OpenRouter API authentication failed

Authentication failed: Error code: 401 - {'error': {'message': 'User not found.', 'code': 401}}

ACTIONS REQUIRED:
1. Check your API key in .env file:
   OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE

2. Verify your API key is valid:
   - Visit: https://openrouter.ai/keys
   - Check if key is active
   - Verify you have credits

3. Test your API key:
   python test_api.py

4. Once fixed, resume processing:
   python main.py --brand "Dafi_Iran" --website "https://dafiiran.com/"

Progress has been saved. You won't lose any work.
═══════════════════════════════════════════════════════════════

Process finished with exit code 1
```

---

### **2. Batch Mode**

```bash
python main.py --google-sheets
```

**Process:**
1. Reads all brands from Google Sheet
2. Starts processing brand #1
3. Validates API key on first LLM call
4. If invalid → **saves checkpoint and stops**
5. User fixes API key
6. Resume: `python main.py --google-sheets --resume`

**Example Output (Fails on Brand 47/500):**

```
============================================================
BATCH MODE: Processing brands from Google Sheets
============================================================

[REGISTRY] Loaded: 46 brands tracked (46 success, 0 failed)
Found 500 brands in sheet

[1/500] BrandOne
  [OK] Completed in 42.3s

[2/500] BrandTwo
  [OK] Completed in 38.7s

...

[47/500] ProblematicBrand
  [RUN] Reason: new_brand
  Website: https://example.com

Validating OpenRouter API key...

============================================================
API KEY ERROR - STOPPING BATCH PROCESSING
============================================================
Failed on brand 47/500: ProblematicBrand
Processed 46 brands before error

Progress saved to: state/checkpoint.json

╔══════════════════════════════════════════════════════════════╗
║                     API KEY ERROR                            ║
╚══════════════════════════════════════════════════════════════╝

❌ OpenRouter API authentication failed

Authentication failed during API call: Error code: 401

ACTIONS REQUIRED:
1. Check your API key in .env file:
   OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE

2. Verify your API key is valid:
   - Visit: https://openrouter.ai/keys
   - Check if key is active
   - Verify you have credits

3. Test your API key:
   python test_api.py

4. Once fixed, resume processing:
   python main.py --google-sheets --resume

Progress has been saved. You won't lose any work.
═══════════════════════════════════════════════════════════════

Process finished with exit code 1
```

---

## 💾 Checkpoint System

### **What Gets Saved:**

When API key error occurs during batch processing, the system saves:

```json
// state/checkpoint.json
{
  "timestamp": "2026-02-17T15:32:45Z",
  "error": "API_KEY_ERROR",
  "failed_brand": "ProblematicBrand",
  "failed_brand_index": 47,
  "processed_count": 46,
  "results": {
    "success": [
      {"brand": "BrandOne", "row": 2, "outputs": {...}},
      {"brand": "BrandTwo", "row": 3, "outputs": {...}},
      // ... 44 more
    ],
    "failed": [],
    "skipped": []
  }
}
```

### **Resume After Fix:**

```bash
# 1. Fix API key in .env
nano .env
# Update: OPENROUTER_API_KEY=sk-or-v1-NEW_KEY

# 2. Test API key
python test_api.py

# 3. Resume from checkpoint
python main.py --google-sheets --resume

# Output:
# [RESUME] Found checkpoint: 46 brands already processed
# [RESUME] Continuing from brand 47/500
# [47/500] ProblematicBrand
#   [OK] Completed in 41.2s
# ...
```

---

## 🔧 Configuration

### **Enable/Disable Fail Fast** (Optional Enhancement)

If you want to allow rule-based fallback in some cases:

```bash
# In .env
FAIL_FAST_ON_API_ERROR=true  # Default: stops immediately
# or
FAIL_FAST_ON_API_ERROR=false  # Allows rule-based fallback
```

**Current Implementation:** Always fails fast (no configuration needed)

---

## 🧪 Testing

### **Test API Key Validation:**

```bash
# Test with valid key
python test_api.py

# Output:
# Testing OpenRouter API...
# API Key: sk-or-v1-abc123...
# Testing model: google/gemini-3-flash-preview
#   SUCCESS: OK
```

### **Test with Invalid Key:**

```bash
# Temporarily set invalid key
export OPENROUTER_API_KEY=sk-or-v1-invalid

# Run test
python test_api.py

# Output:
# Testing model: google/gemini-3-flash-preview
#   401 Authentication Error
#   Message: User not found (API key invalid)
```

### **Test Single Brand:**

```bash
# With invalid key
python main.py --brand "TestBrand"

# Should stop immediately with clear error message
```

---

## 📊 Error Types

### **1. API Key Not Configured**

```python
# .env
OPENROUTER_API_KEY=

# Error:
APIKeyError: Cannot generate: API key not configured or invalid
```

**Fix:** Add API key to `.env`

---

### **2. API Key Invalid (401)**

```python
# .env
OPENROUTER_API_KEY=sk-or-v1-wrong-key

# Error:
APIKeyError: Authentication failed: Error code: 401 - User not found
```

**Fix:** Get new API key from https://openrouter.ai/keys

---

### **3. API Key Expired/Revoked**

```python
# Key was valid but got revoked

# Error:
APIKeyError: Authentication failed during API call: User not found
```

**Fix:** Generate new API key

---

### **4. No Credits**

```python
# Key valid but out of credits

# Error:
APIKeyError: Authentication failed: Insufficient credits
```

**Fix:** Add credits to OpenRouter account

---

## 🆚 Before vs After

### **Before (Rule-Based Fallback):**

```
✗ API key invalid
↓
System continues silently
↓
Generates low-quality outputs
  - Empty product_catalog.csv
  - Generic insights
  - Missing sister brands
↓
User discovers issue hours later
↓
Must reprocess everything
```

### **After (Fail Fast):**

```
✗ API key invalid
↓
System stops immediately
↓
Shows clear error message
↓
User fixes API key (2 minutes)
↓
Resumes from checkpoint
↓
High-quality outputs
```

---

## 🎯 Best Practices

### **1. Validate Before Large Batches**

```bash
# Before processing 500 brands:
python test_api.py

# Ensures API key works before starting
```

### **2. Monitor Credits**

- Check OpenRouter balance before large batches
- System will fail if credits run out mid-batch
- Set budget limits: `python main.py --google-sheets --budget 50`

### **3. Use Resume**

```bash
# If batch interrupted:
python main.py --google-sheets --resume

# Don't use --force (reprocesses everything)
```

### **4. Keep Backup API Key**

```bash
# Primary key
OPENROUTER_API_KEY=sk-or-v1-primary-key

# Backup (comment out)
# OPENROUTER_API_KEY=sk-or-v1-backup-key
```

---

## 🐛 Troubleshooting

### **Issue: "API key validation failed" but key is correct**

**Possible causes:**
1. OpenRouter service is down
2. Network connectivity issues
3. Firewall blocking API requests

**Solution:**
```bash
# Test connectivity
curl https://openrouter.ai/api/v1/models

# If fails, check network/firewall
```

---

### **Issue: Checkpoint won't load**

**Possible causes:**
1. Checkpoint file corrupted
2. JSON parsing error

**Solution:**
```bash
# Check checkpoint file
cat state/checkpoint.json

# If corrupted, delete and start fresh
rm state/checkpoint.json
python main.py --google-sheets
```

---

### **Issue: Want to force rule-based mode for testing**

**Solution:**
```bash
# Remove API key temporarily
mv .env .env.backup
cp .env.example .env
# Remove OPENROUTER_API_KEY from .env

# Run without LLM
python main.py --brand "TestBrand"

# Restore
mv .env.backup .env
```

---

## 📝 Summary

| Aspect | Rule-Based Fallback (Old) | Fail Fast (New) |
|--------|---------------------------|-----------------|
| **API Error Detection** | After processing | Before processing |
| **User Notification** | Silent fallback | Clear error message |
| **Output Quality** | Low (empty CSVs) | Consistent high quality |
| **Time Waste** | Hours of bad processing | Stops immediately |
| **Resume Support** | None | Full checkpoint system |
| **Production Ready** | ❌ No | ✅ Yes |

---

## 🚀 Implementation Status

✅ **Completed:**
- Custom `APIKeyError` exception
- LLM client validation method
- API key test call before workflow
- Single brand error handling
- Batch mode error handling
- Checkpoint save on error
- Clear error messages with instructions
- Resume from checkpoint support

🎯 **Ready for Production**

---

**Last Updated:** 2026-02-17
**Version:** 2.0
