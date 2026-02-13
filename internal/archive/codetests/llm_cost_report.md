# LLM Cost Assessment Report

**Project:** `C:\Users\andreaskretschmer\OneDrive - Nagarro\Dokumente\_CODE\analytics-usecase-library`
**Assessment Version:** 2.0.0
**Generated:** 2026-02-13T09:57:50.340420

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Files Scanned | 6 |
| Files with LLM Usage | 1 |
| Total Issues | 48 |

### Issues by Severity

| Severity | Count | Action |
|----------|-------|--------|
| 🔴 Critical | 2 | Fix immediately |
| 🟠 High | 8 | Fix this week |
| 🟡 Medium | 38 | Plan to fix |
| 🟢 Low | 0 | Consider fixing |

### Estimated Savings

**Potential 50-70% cost reduction by addressing critical issues**

---

## Top Recommendations

1. [2 issues] Batch requests or use parallel processing
2. [8 issues] Add max_tokens to all API calls
3. [13 issues] Evaluate cheaper models for simpler tasks

---

## Issues by Category

- **Missing Error Handling**: 15 issue(s)
- **Expensive Model Usage**: 13 issue(s)
- **No Streaming**: 10 issue(s)
- **No Token Limit**: 8 issue(s)
- **API Calls in Loop**: 2 issue(s)

---

## Files with Most Issues

- `codetests\llm_cost_assessment.py`: 48 issue(s)

---

## Detailed Findings

### 🔴 CRITICAL Priority Issues (2)

#### API Calls in Loop

**File:** `codetests\llm_cost_assessment.py` (line 527)
**Confidence:** ✓ High confidence

```
result = client.chat.completions.create(...)
```

**Issue:** LLM API call detected inside a loop. This pattern can result in many expensive API calls, multiplying costs by the number of iterations.

**Recommendation:**

Refactor to batch or parallelize:

```python
# BAD: N API calls
for item in items:
    result = client.chat.completions.create(...)

# GOOD Option 1: Batch into single prompt
batch_prompt = "Process each item:\n" + "\n".join(items)
result = client.chat.completions.create(
    messages=[{"role": "user", "content": batch_prompt}]
)

# GOOD Option 2: Parallel async calls
import asyncio

async def process_item(item):
    return await async_client.chat.completions.create(...)

results = await asyncio.gather(*[process_item(item) for item in items])

# GOOD Option 3: Use OpenAI Batch API for non-urgent processing
# 50% cost reduction for batch jobs
```

Also consider:
- Do all items really need LLM processing?
- Can you filter/pre-process before calling the API?
- Cache results to avoid duplicate processing

**Potential Savings:** 50-95% by batching or eliminating redundant calls

---

#### API Calls in Loop

**File:** `codetests\llm_cost_assessment.py` (line 641)
**Confidence:** ✓ High confidence

```
result = client.chat.completions.create(
```

**Issue:** LLM API call detected inside a loop. This pattern can result in many expensive API calls, multiplying costs by the number of iterations.

**Recommendation:**

Refactor to batch or parallelize:

```python
# BAD: N API calls
for item in items:
    result = client.chat.completions.create(...)

# GOOD Option 1: Batch into single prompt
batch_prompt = "Process each item:\n" + "\n".join(items)
result = client.chat.completions.create(
    messages=[{"role": "user", "content": batch_prompt}]
)

# GOOD Option 2: Parallel async calls
import asyncio

async def process_item(item):
    return await async_client.chat.completions.create(...)

results = await asyncio.gather(*[process_item(item) for item in items])

# GOOD Option 3: Use OpenAI Batch API for non-urgent processing
# 50% cost reduction for batch jobs
```

Also consider:
- Do all items really need LLM processing?
- Can you filter/pre-process before calling the API?
- Cache results to avoid duplicate processing

**Potential Savings:** 50-95% by batching or eliminating redundant calls

---

### 🟠 HIGH Priority Issues (8)

#### No Token Limit

**File:** `codetests\llm_cost_assessment.py` (line 527)
**Confidence:** ✓ High confidence

```
result = client.chat.completions.create(...)
```

**Issue:** API call without max_tokens parameter. The model may generate excessive tokens, increasing costs unpredictably.

**Recommendation:**

Add max_tokens parameter to limit response length:

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    max_tokens=500  # Adjust based on expected response length
)
```

Guidelines for max_tokens:
- Simple yes/no or classification: 10-50 tokens
- Short answers: 100-300 tokens
- Paragraphs: 300-800 tokens
- Long-form content: 1000-2000 tokens

**Potential Savings:** 20-40% token reduction

---

#### No Token Limit

**File:** `codetests\llm_cost_assessment.py` (line 531)
**Confidence:** ✓ High confidence

```
result = client.chat.completions.create(
```

**Issue:** API call without max_tokens parameter. The model may generate excessive tokens, increasing costs unpredictably.

**Recommendation:**

Add max_tokens parameter to limit response length:

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    max_tokens=500  # Adjust based on expected response length
)
```

Guidelines for max_tokens:
- Simple yes/no or classification: 10-50 tokens
- Short answers: 100-300 tokens
- Paragraphs: 300-800 tokens
- Long-form content: 1000-2000 tokens

**Potential Savings:** 20-40% token reduction

---

#### No Token Limit

**File:** `codetests\llm_cost_assessment.py` (line 539)
**Confidence:** ✓ High confidence

```
return await async_client.chat.completions.create(...)
```

**Issue:** API call without max_tokens parameter. The model may generate excessive tokens, increasing costs unpredictably.

**Recommendation:**

Add max_tokens parameter to limit response length:

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    max_tokens=500  # Adjust based on expected response length
)
```

Guidelines for max_tokens:
- Simple yes/no or classification: 10-50 tokens
- Short answers: 100-300 tokens
- Paragraphs: 300-800 tokens
- Long-form content: 1000-2000 tokens

**Potential Savings:** 20-40% token reduction

---

#### No Token Limit

**File:** `codetests\llm_cost_assessment.py` (line 877)
**Confidence:** ✓ High confidence

```
response = client.chat.completions.create(
```

**Issue:** API call without max_tokens parameter. The model may generate excessive tokens, increasing costs unpredictably.

**Recommendation:**

Add max_tokens parameter to limit response length:

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    max_tokens=500  # Adjust based on expected response length
)
```

Guidelines for max_tokens:
- Simple yes/no or classification: 10-50 tokens
- Short answers: 100-300 tokens
- Paragraphs: 300-800 tokens
- Long-form content: 1000-2000 tokens

**Potential Savings:** 20-40% token reduction

---

#### No Token Limit

**File:** `codetests\llm_cost_assessment.py` (line 942)
**Confidence:** ✓ High confidence

```
response = client.embeddings.create(
```

**Issue:** API call without max_tokens parameter. The model may generate excessive tokens, increasing costs unpredictably.

**Recommendation:**

Add max_tokens parameter to limit response length:

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    max_tokens=500  # Adjust based on expected response length
)
```

Guidelines for max_tokens:
- Simple yes/no or classification: 10-50 tokens
- Short answers: 100-300 tokens
- Paragraphs: 300-800 tokens
- Long-form content: 1000-2000 tokens

**Potential Savings:** 20-40% token reduction

---

#### No Token Limit

**File:** `codetests\llm_cost_assessment.py` (line 1047)
**Confidence:** ✓ High confidence

```
lambda: client.chat.completions.create(...)
```

**Issue:** API call without max_tokens parameter. The model may generate excessive tokens, increasing costs unpredictably.

**Recommendation:**

Add max_tokens parameter to limit response length:

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    max_tokens=500  # Adjust based on expected response length
)
```

Guidelines for max_tokens:
- Simple yes/no or classification: 10-50 tokens
- Short answers: 100-300 tokens
- Paragraphs: 300-800 tokens
- Long-form content: 1000-2000 tokens

**Potential Savings:** 20-40% token reduction

---

#### No Token Limit

**File:** `codetests\llm_cost_assessment.py` (line 1057)
**Confidence:** ✓ High confidence

```
return client.chat.completions.create(messages=messages)
```

**Issue:** API call without max_tokens parameter. The model may generate excessive tokens, increasing costs unpredictably.

**Recommendation:**

Add max_tokens parameter to limit response length:

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    max_tokens=500  # Adjust based on expected response length
)
```

Guidelines for max_tokens:
- Simple yes/no or classification: 10-50 tokens
- Short answers: 100-300 tokens
- Paragraphs: 300-800 tokens
- Long-form content: 1000-2000 tokens

**Potential Savings:** 20-40% token reduction

---

#### No Token Limit

**File:** `codetests\llm_cost_assessment.py` (line 1392)
**Confidence:** ✓ High confidence

```
return client.chat.completions.create(...)
```

**Issue:** API call without max_tokens parameter. The model may generate excessive tokens, increasing costs unpredictably.

**Recommendation:**

Add max_tokens parameter to limit response length:

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    max_tokens=500  # Adjust based on expected response length
)
```

Guidelines for max_tokens:
- Simple yes/no or classification: 10-50 tokens
- Short answers: 100-300 tokens
- Paragraphs: 300-800 tokens
- Long-form content: 1000-2000 tokens

**Potential Savings:** 20-40% token reduction

---

### 🟡 MEDIUM Priority Issues (38)

#### Expensive Model Usage

**File:** `codetests\llm_cost_assessment.py` (line 195)
**Confidence:** ~ Low confidence

```
model="gpt-4",
```

**Issue:** Using gpt-4. Consider if gpt-4o-mini or gpt-3.5-turbo would work for this task.

**Recommendation:**

Match model to task complexity:

```python
def select_model(task_type: str) -> str:
    '''Select appropriate model based on task.'''
    MODELS = {
        # Simple tasks: classification, extraction, formatting
        "simple": "gpt-3.5-turbo",       # $0.0005/1K input

        # Medium tasks: general Q&A, summarization
        "medium": "gpt-4o-mini",          # $0.00015/1K input

        # Complex tasks: reasoning, analysis, code generation
        "complex": "gpt-4o",              # $0.005/1K input

        # Most complex: multi-step reasoning, research
        "advanced": "gpt-4-turbo",        # $0.01/1K input
    }
    return MODELS.get(task_type, "gpt-4o-mini")

# Task classification examples:
# - Sentiment analysis → simple
# - Text extraction → simple
# - Summarization → medium
# - Translation → medium
# - Code review → complex
# - Architecture design → advanced
```

Cost comparison (per 1M tokens input):
- gpt-3.5-turbo: $0.50
- gpt-4o-mini: $0.15
- gpt-4o: $5.00
- gpt-4-turbo: $10.00
- gpt-4: $30.00

**Potential Savings:** 50-95% per request by using appropriate model tier

---

#### Expensive Model Usage

**File:** `codetests\llm_cost_assessment.py` (line 716)
**Confidence:** ~ Low confidence

```
def count_tokens(text: str, model: str = "gpt-4") -> int:
```

**Issue:** Using gpt-4. Consider if gpt-4o-mini or gpt-3.5-turbo would work for this task.

**Recommendation:**

Match model to task complexity:

```python
def select_model(task_type: str) -> str:
    '''Select appropriate model based on task.'''
    MODELS = {
        # Simple tasks: classification, extraction, formatting
        "simple": "gpt-3.5-turbo",       # $0.0005/1K input

        # Medium tasks: general Q&A, summarization
        "medium": "gpt-4o-mini",          # $0.00015/1K input

        # Complex tasks: reasoning, analysis, code generation
        "complex": "gpt-4o",              # $0.005/1K input

        # Most complex: multi-step reasoning, research
        "advanced": "gpt-4-turbo",        # $0.01/1K input
    }
    return MODELS.get(task_type, "gpt-4o-mini")

# Task classification examples:
# - Sentiment analysis → simple
# - Text extraction → simple
# - Summarization → medium
# - Translation → medium
# - Code review → complex
# - Architecture design → advanced
```

Cost comparison (per 1M tokens input):
- gpt-3.5-turbo: $0.50
- gpt-4o-mini: $0.15
- gpt-4o: $5.00
- gpt-4-turbo: $10.00
- gpt-4: $30.00

**Potential Savings:** 50-95% per request by using appropriate model tier

---

#### Expensive Model Usage

**File:** `codetests\llm_cost_assessment.py` (line 724)
**Confidence:** ~ Low confidence

```
def estimate_cost(messages: list, model: str = "gpt-4") -> dict:
```

**Issue:** Using gpt-4. Consider if gpt-4o-mini or gpt-3.5-turbo would work for this task.

**Recommendation:**

Match model to task complexity:

```python
def select_model(task_type: str) -> str:
    '''Select appropriate model based on task.'''
    MODELS = {
        # Simple tasks: classification, extraction, formatting
        "simple": "gpt-3.5-turbo",       # $0.0005/1K input

        # Medium tasks: general Q&A, summarization
        "medium": "gpt-4o-mini",          # $0.00015/1K input

        # Complex tasks: reasoning, analysis, code generation
        "complex": "gpt-4o",              # $0.005/1K input

        # Most complex: multi-step reasoning, research
        "advanced": "gpt-4-turbo",        # $0.01/1K input
    }
    return MODELS.get(task_type, "gpt-4o-mini")

# Task classification examples:
# - Sentiment analysis → simple
# - Text extraction → simple
# - Summarization → medium
# - Translation → medium
# - Code review → complex
# - Architecture design → advanced
```

Cost comparison (per 1M tokens input):
- gpt-3.5-turbo: $0.50
- gpt-4o-mini: $0.15
- gpt-4o: $5.00
- gpt-4-turbo: $10.00
- gpt-4: $30.00

**Potential Savings:** 50-95% per request by using appropriate model tier

---

#### Expensive Model Usage

**File:** `codetests\llm_cost_assessment.py` (line 735)
**Confidence:** ~ Low confidence

```
prices = PRICES_PER_1K.get(model, PRICES_PER_1K["gpt-4"])
```

**Issue:** Using gpt-4. Consider if gpt-4o-mini or gpt-3.5-turbo would work for this task.

**Recommendation:**

Match model to task complexity:

```python
def select_model(task_type: str) -> str:
    '''Select appropriate model based on task.'''
    MODELS = {
        # Simple tasks: classification, extraction, formatting
        "simple": "gpt-3.5-turbo",       # $0.0005/1K input

        # Medium tasks: general Q&A, summarization
        "medium": "gpt-4o-mini",          # $0.00015/1K input

        # Complex tasks: reasoning, analysis, code generation
        "complex": "gpt-4o",              # $0.005/1K input

        # Most complex: multi-step reasoning, research
        "advanced": "gpt-4-turbo",        # $0.01/1K input
    }
    return MODELS.get(task_type, "gpt-4o-mini")

# Task classification examples:
# - Sentiment analysis → simple
# - Text extraction → simple
# - Summarization → medium
# - Translation → medium
# - Code review → complex
# - Architecture design → advanced
```

Cost comparison (per 1M tokens input):
- gpt-3.5-turbo: $0.50
- gpt-4o-mini: $0.15
- gpt-4o: $5.00
- gpt-4-turbo: $10.00
- gpt-4: $30.00

**Potential Savings:** 50-95% per request by using appropriate model tier

---

#### Expensive Model Usage

**File:** `codetests\llm_cost_assessment.py` (line 813)
**Confidence:** ~ Low confidence

```
"advanced": "gpt-4-turbo",        # $0.01/1K input
```

**Issue:** Using gpt-4. Consider if gpt-4o-mini or gpt-3.5-turbo would work for this task.

**Recommendation:**

Match model to task complexity:

```python
def select_model(task_type: str) -> str:
    '''Select appropriate model based on task.'''
    MODELS = {
        # Simple tasks: classification, extraction, formatting
        "simple": "gpt-3.5-turbo",       # $0.0005/1K input

        # Medium tasks: general Q&A, summarization
        "medium": "gpt-4o-mini",          # $0.00015/1K input

        # Complex tasks: reasoning, analysis, code generation
        "complex": "gpt-4o",              # $0.005/1K input

        # Most complex: multi-step reasoning, research
        "advanced": "gpt-4-turbo",        # $0.01/1K input
    }
    return MODELS.get(task_type, "gpt-4o-mini")

# Task classification examples:
# - Sentiment analysis → simple
# - Text extraction → simple
# - Summarization → medium
# - Translation → medium
# - Code review → complex
# - Architecture design → advanced
```

Cost comparison (per 1M tokens input):
- gpt-3.5-turbo: $0.50
- gpt-4o-mini: $0.15
- gpt-4o: $5.00
- gpt-4-turbo: $10.00
- gpt-4: $30.00

**Potential Savings:** 50-95% per request by using appropriate model tier

---

#### Expensive Model Usage

**File:** `codetests\llm_cost_assessment.py` (line 815)
**Confidence:** ~ Low confidence

```
return MODELS.get(task_type, "gpt-4o-mini")
```

**Issue:** Using gpt-4. Consider if gpt-4o-mini or gpt-3.5-turbo would work for this task.

**Recommendation:**

Match model to task complexity:

```python
def select_model(task_type: str) -> str:
    '''Select appropriate model based on task.'''
    MODELS = {
        # Simple tasks: classification, extraction, formatting
        "simple": "gpt-3.5-turbo",       # $0.0005/1K input

        # Medium tasks: general Q&A, summarization
        "medium": "gpt-4o-mini",          # $0.00015/1K input

        # Complex tasks: reasoning, analysis, code generation
        "complex": "gpt-4o",              # $0.005/1K input

        # Most complex: multi-step reasoning, research
        "advanced": "gpt-4-turbo",        # $0.01/1K input
    }
    return MODELS.get(task_type, "gpt-4o-mini")

# Task classification examples:
# - Sentiment analysis → simple
# - Text extraction → simple
# - Summarization → medium
# - Translation → medium
# - Code review → complex
# - Architecture design → advanced
```

Cost comparison (per 1M tokens input):
- gpt-3.5-turbo: $0.50
- gpt-4o-mini: $0.15
- gpt-4o: $5.00
- gpt-4-turbo: $10.00
- gpt-4: $30.00

**Potential Savings:** 50-95% per request by using appropriate model tier

---

#### Expensive Model Usage

**File:** `codetests\llm_cost_assessment.py` (line 830)
**Confidence:** ~ Low confidence

```
- gpt-4-turbo: $10.00
```

**Issue:** Using gpt-4. Consider if gpt-4o-mini or gpt-3.5-turbo would work for this task.

**Recommendation:**

Match model to task complexity:

```python
def select_model(task_type: str) -> str:
    '''Select appropriate model based on task.'''
    MODELS = {
        # Simple tasks: classification, extraction, formatting
        "simple": "gpt-3.5-turbo",       # $0.0005/1K input

        # Medium tasks: general Q&A, summarization
        "medium": "gpt-4o-mini",          # $0.00015/1K input

        # Complex tasks: reasoning, analysis, code generation
        "complex": "gpt-4o",              # $0.005/1K input

        # Most complex: multi-step reasoning, research
        "advanced": "gpt-4-turbo",        # $0.01/1K input
    }
    return MODELS.get(task_type, "gpt-4o-mini")

# Task classification examples:
# - Sentiment analysis → simple
# - Text extraction → simple
# - Summarization → medium
# - Translation → medium
# - Code review → complex
# - Architecture design → advanced
```

Cost comparison (per 1M tokens input):
- gpt-3.5-turbo: $0.50
- gpt-4o-mini: $0.15
- gpt-4o: $5.00
- gpt-4-turbo: $10.00
- gpt-4: $30.00

**Potential Savings:** 50-95% per request by using appropriate model tier

---

#### Expensive Model Usage

**File:** `codetests\llm_cost_assessment.py` (line 831)
**Confidence:** ~ Low confidence

```
- gpt-4: $30.00"""
```

**Issue:** Using gpt-4. Consider if gpt-4o-mini or gpt-3.5-turbo would work for this task.

**Recommendation:**

Match model to task complexity:

```python
def select_model(task_type: str) -> str:
    '''Select appropriate model based on task.'''
    MODELS = {
        # Simple tasks: classification, extraction, formatting
        "simple": "gpt-3.5-turbo",       # $0.0005/1K input

        # Medium tasks: general Q&A, summarization
        "medium": "gpt-4o-mini",          # $0.00015/1K input

        # Complex tasks: reasoning, analysis, code generation
        "complex": "gpt-4o",              # $0.005/1K input

        # Most complex: multi-step reasoning, research
        "advanced": "gpt-4-turbo",        # $0.01/1K input
    }
    return MODELS.get(task_type, "gpt-4o-mini")

# Task classification examples:
# - Sentiment analysis → simple
# - Text extraction → simple
# - Summarization → medium
# - Translation → medium
# - Code review → complex
# - Architecture design → advanced
```

Cost comparison (per 1M tokens input):
- gpt-3.5-turbo: $0.50
- gpt-4o-mini: $0.15
- gpt-4o: $5.00
- gpt-4-turbo: $10.00
- gpt-4: $30.00

**Potential Savings:** 50-95% per request by using appropriate model tier

---

#### Expensive Model Usage

**File:** `codetests\llm_cost_assessment.py` (line 835)
**Confidence:** ~ Low confidence

```
'gpt-4': 'gpt-4o-mini or gpt-3.5-turbo',
```

**Issue:** Using gpt-4. Consider if gpt-4o-mini or gpt-3.5-turbo would work for this task.

**Recommendation:**

Match model to task complexity:

```python
def select_model(task_type: str) -> str:
    '''Select appropriate model based on task.'''
    MODELS = {
        # Simple tasks: classification, extraction, formatting
        "simple": "gpt-3.5-turbo",       # $0.0005/1K input

        # Medium tasks: general Q&A, summarization
        "medium": "gpt-4o-mini",          # $0.00015/1K input

        # Complex tasks: reasoning, analysis, code generation
        "complex": "gpt-4o",              # $0.005/1K input

        # Most complex: multi-step reasoning, research
        "advanced": "gpt-4-turbo",        # $0.01/1K input
    }
    return MODELS.get(task_type, "gpt-4o-mini")

# Task classification examples:
# - Sentiment analysis → simple
# - Text extraction → simple
# - Summarization → medium
# - Translation → medium
# - Code review → complex
# - Architecture design → advanced
```

Cost comparison (per 1M tokens input):
- gpt-3.5-turbo: $0.50
- gpt-4o-mini: $0.15
- gpt-4o: $5.00
- gpt-4-turbo: $10.00
- gpt-4: $30.00

**Potential Savings:** 50-95% per request by using appropriate model tier

---

#### Expensive Model Usage

**File:** `codetests\llm_cost_assessment.py` (line 836)
**Confidence:** ~ Low confidence

```
'gpt-4-32k': 'gpt-4o or gpt-4-turbo',
```

**Issue:** Using gpt-4. Consider if gpt-4o-mini or gpt-3.5-turbo would work for this task.

**Recommendation:**

Match model to task complexity:

```python
def select_model(task_type: str) -> str:
    '''Select appropriate model based on task.'''
    MODELS = {
        # Simple tasks: classification, extraction, formatting
        "simple": "gpt-3.5-turbo",       # $0.0005/1K input

        # Medium tasks: general Q&A, summarization
        "medium": "gpt-4o-mini",          # $0.00015/1K input

        # Complex tasks: reasoning, analysis, code generation
        "complex": "gpt-4o",              # $0.005/1K input

        # Most complex: multi-step reasoning, research
        "advanced": "gpt-4-turbo",        # $0.01/1K input
    }
    return MODELS.get(task_type, "gpt-4o-mini")

# Task classification examples:
# - Sentiment analysis → simple
# - Text extraction → simple
# - Summarization → medium
# - Translation → medium
# - Code review → complex
# - Architecture design → advanced
```

Cost comparison (per 1M tokens input):
- gpt-3.5-turbo: $0.50
- gpt-4o-mini: $0.15
- gpt-4o: $5.00
- gpt-4-turbo: $10.00
- gpt-4: $30.00

**Potential Savings:** 50-95% per request by using appropriate model tier

---

#### Expensive Model Usage

**File:** `codetests\llm_cost_assessment.py` (line 878)
**Confidence:** ~ Low confidence

```
model="gpt-4",
```

**Issue:** Using gpt-4. Consider if gpt-4o-mini or gpt-3.5-turbo would work for this task.

**Recommendation:**

Match model to task complexity:

```python
def select_model(task_type: str) -> str:
    '''Select appropriate model based on task.'''
    MODELS = {
        # Simple tasks: classification, extraction, formatting
        "simple": "gpt-3.5-turbo",       # $0.0005/1K input

        # Medium tasks: general Q&A, summarization
        "medium": "gpt-4o-mini",          # $0.00015/1K input

        # Complex tasks: reasoning, analysis, code generation
        "complex": "gpt-4o",              # $0.005/1K input

        # Most complex: multi-step reasoning, research
        "advanced": "gpt-4-turbo",        # $0.01/1K input
    }
    return MODELS.get(task_type, "gpt-4o-mini")

# Task classification examples:
# - Sentiment analysis → simple
# - Text extraction → simple
# - Summarization → medium
# - Translation → medium
# - Code review → complex
# - Architecture design → advanced
```

Cost comparison (per 1M tokens input):
- gpt-3.5-turbo: $0.50
- gpt-4o-mini: $0.15
- gpt-4o: $5.00
- gpt-4-turbo: $10.00
- gpt-4: $30.00

**Potential Savings:** 50-95% per request by using appropriate model tier

---

#### Expensive Model Usage

**File:** `codetests\llm_cost_assessment.py` (line 1379)
**Confidence:** ~ Low confidence

```
model="gpt-4",
```

**Issue:** Using gpt-4. Consider if gpt-4o-mini or gpt-3.5-turbo would work for this task.

**Recommendation:**

Match model to task complexity:

```python
def select_model(task_type: str) -> str:
    '''Select appropriate model based on task.'''
    MODELS = {
        # Simple tasks: classification, extraction, formatting
        "simple": "gpt-3.5-turbo",       # $0.0005/1K input

        # Medium tasks: general Q&A, summarization
        "medium": "gpt-4o-mini",          # $0.00015/1K input

        # Complex tasks: reasoning, analysis, code generation
        "complex": "gpt-4o",              # $0.005/1K input

        # Most complex: multi-step reasoning, research
        "advanced": "gpt-4-turbo",        # $0.01/1K input
    }
    return MODELS.get(task_type, "gpt-4o-mini")

# Task classification examples:
# - Sentiment analysis → simple
# - Text extraction → simple
# - Summarization → medium
# - Translation → medium
# - Code review → complex
# - Architecture design → advanced
```

Cost comparison (per 1M tokens input):
- gpt-3.5-turbo: $0.50
- gpt-4o-mini: $0.15
- gpt-4o: $5.00
- gpt-4-turbo: $10.00
- gpt-4: $30.00

**Potential Savings:** 50-95% per request by using appropriate model tier

---

#### Expensive Model Usage

**File:** `codetests\llm_cost_assessment.py` (line 1411)
**Confidence:** ~ Low confidence

```
enc = tiktoken.encoding_for_model("gpt-4")
```

**Issue:** Using gpt-4. Consider if gpt-4o-mini or gpt-3.5-turbo would work for this task.

**Recommendation:**

Match model to task complexity:

```python
def select_model(task_type: str) -> str:
    '''Select appropriate model based on task.'''
    MODELS = {
        # Simple tasks: classification, extraction, formatting
        "simple": "gpt-3.5-turbo",       # $0.0005/1K input

        # Medium tasks: general Q&A, summarization
        "medium": "gpt-4o-mini",          # $0.00015/1K input

        # Complex tasks: reasoning, analysis, code generation
        "complex": "gpt-4o",              # $0.005/1K input

        # Most complex: multi-step reasoning, research
        "advanced": "gpt-4-turbo",        # $0.01/1K input
    }
    return MODELS.get(task_type, "gpt-4o-mini")

# Task classification examples:
# - Sentiment analysis → simple
# - Text extraction → simple
# - Summarization → medium
# - Translation → medium
# - Code review → complex
# - Architecture design → advanced
```

Cost comparison (per 1M tokens input):
- gpt-3.5-turbo: $0.50
- gpt-4o-mini: $0.15
- gpt-4o: $5.00
- gpt-4-turbo: $10.00
- gpt-4: $30.00

**Potential Savings:** 50-95% per request by using appropriate model tier

---

#### No Streaming

**File:** `codetests\llm_cost_assessment.py` (line 194)
**Confidence:** ~ Low confidence

```
response = client.chat.completions.create(
```

**Issue:** API call without streaming enabled. For long responses, streaming improves user experience and allows early termination if the response isn't needed.

**Recommendation:**

Enable streaming for better UX and potential cost savings:

```python
# Streaming allows users to cancel early, saving tokens
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    stream=True  # Enable streaming
)

# Process streamed response
full_response = ""
for chunk in response:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        print(content, end="", flush=True)  # Show to user immediately
        full_response += content

        # Option: Allow early termination
        if user_cancelled():
            break  # Stop receiving (saves remaining tokens)
```

Benefits:
- Better UX (user sees response immediately)
- Can stop generation early if response is wrong
- Reduces perceived latency

**Potential Savings:** 10-30% if users cancel early; improved UX always

---

#### No Streaming

**File:** `codetests\llm_cost_assessment.py` (line 527)
**Confidence:** ~ Low confidence

```
result = client.chat.completions.create(...)
```

**Issue:** API call without streaming enabled. For long responses, streaming improves user experience and allows early termination if the response isn't needed.

**Recommendation:**

Enable streaming for better UX and potential cost savings:

```python
# Streaming allows users to cancel early, saving tokens
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    stream=True  # Enable streaming
)

# Process streamed response
full_response = ""
for chunk in response:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        print(content, end="", flush=True)  # Show to user immediately
        full_response += content

        # Option: Allow early termination
        if user_cancelled():
            break  # Stop receiving (saves remaining tokens)
```

Benefits:
- Better UX (user sees response immediately)
- Can stop generation early if response is wrong
- Reduces perceived latency

**Potential Savings:** 10-30% if users cancel early; improved UX always

---

#### No Streaming

**File:** `codetests\llm_cost_assessment.py` (line 531)
**Confidence:** ~ Low confidence

```
result = client.chat.completions.create(
```

**Issue:** API call without streaming enabled. For long responses, streaming improves user experience and allows early termination if the response isn't needed.

**Recommendation:**

Enable streaming for better UX and potential cost savings:

```python
# Streaming allows users to cancel early, saving tokens
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    stream=True  # Enable streaming
)

# Process streamed response
full_response = ""
for chunk in response:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        print(content, end="", flush=True)  # Show to user immediately
        full_response += content

        # Option: Allow early termination
        if user_cancelled():
            break  # Stop receiving (saves remaining tokens)
```

Benefits:
- Better UX (user sees response immediately)
- Can stop generation early if response is wrong
- Reduces perceived latency

**Potential Savings:** 10-30% if users cancel early; improved UX always

---

#### No Streaming

**File:** `codetests\llm_cost_assessment.py` (line 539)
**Confidence:** ~ Low confidence

```
return await async_client.chat.completions.create(...)
```

**Issue:** API call without streaming enabled. For long responses, streaming improves user experience and allows early termination if the response isn't needed.

**Recommendation:**

Enable streaming for better UX and potential cost savings:

```python
# Streaming allows users to cancel early, saving tokens
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    stream=True  # Enable streaming
)

# Process streamed response
full_response = ""
for chunk in response:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        print(content, end="", flush=True)  # Show to user immediately
        full_response += content

        # Option: Allow early termination
        if user_cancelled():
            break  # Stop receiving (saves remaining tokens)
```

Benefits:
- Better UX (user sees response immediately)
- Can stop generation early if response is wrong
- Reduces perceived latency

**Potential Savings:** 10-30% if users cancel early; improved UX always

---

#### No Streaming

**File:** `codetests\llm_cost_assessment.py` (line 641)
**Confidence:** ~ Low confidence

```
result = client.chat.completions.create(
```

**Issue:** API call without streaming enabled. For long responses, streaming improves user experience and allows early termination if the response isn't needed.

**Recommendation:**

Enable streaming for better UX and potential cost savings:

```python
# Streaming allows users to cancel early, saving tokens
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    stream=True  # Enable streaming
)

# Process streamed response
full_response = ""
for chunk in response:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        print(content, end="", flush=True)  # Show to user immediately
        full_response += content

        # Option: Allow early termination
        if user_cancelled():
            break  # Stop receiving (saves remaining tokens)
```

Benefits:
- Better UX (user sees response immediately)
- Can stop generation early if response is wrong
- Reduces perceived latency

**Potential Savings:** 10-30% if users cancel early; improved UX always

---

#### No Streaming

**File:** `codetests\llm_cost_assessment.py` (line 942)
**Confidence:** ~ Low confidence

```
response = client.embeddings.create(
```

**Issue:** API call without streaming enabled. For long responses, streaming improves user experience and allows early termination if the response isn't needed.

**Recommendation:**

Enable streaming for better UX and potential cost savings:

```python
# Streaming allows users to cancel early, saving tokens
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    stream=True  # Enable streaming
)

# Process streamed response
full_response = ""
for chunk in response:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        print(content, end="", flush=True)  # Show to user immediately
        full_response += content

        # Option: Allow early termination
        if user_cancelled():
            break  # Stop receiving (saves remaining tokens)
```

Benefits:
- Better UX (user sees response immediately)
- Can stop generation early if response is wrong
- Reduces perceived latency

**Potential Savings:** 10-30% if users cancel early; improved UX always

---

#### No Streaming

**File:** `codetests\llm_cost_assessment.py` (line 1047)
**Confidence:** ~ Low confidence

```
lambda: client.chat.completions.create(...)
```

**Issue:** API call without streaming enabled. For long responses, streaming improves user experience and allows early termination if the response isn't needed.

**Recommendation:**

Enable streaming for better UX and potential cost savings:

```python
# Streaming allows users to cancel early, saving tokens
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    stream=True  # Enable streaming
)

# Process streamed response
full_response = ""
for chunk in response:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        print(content, end="", flush=True)  # Show to user immediately
        full_response += content

        # Option: Allow early termination
        if user_cancelled():
            break  # Stop receiving (saves remaining tokens)
```

Benefits:
- Better UX (user sees response immediately)
- Can stop generation early if response is wrong
- Reduces perceived latency

**Potential Savings:** 10-30% if users cancel early; improved UX always

---

#### No Streaming

**File:** `codetests\llm_cost_assessment.py` (line 1057)
**Confidence:** ~ Low confidence

```
return client.chat.completions.create(messages=messages)
```

**Issue:** API call without streaming enabled. For long responses, streaming improves user experience and allows early termination if the response isn't needed.

**Recommendation:**

Enable streaming for better UX and potential cost savings:

```python
# Streaming allows users to cancel early, saving tokens
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    stream=True  # Enable streaming
)

# Process streamed response
full_response = ""
for chunk in response:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        print(content, end="", flush=True)  # Show to user immediately
        full_response += content

        # Option: Allow early termination
        if user_cancelled():
            break  # Stop receiving (saves remaining tokens)
```

Benefits:
- Better UX (user sees response immediately)
- Can stop generation early if response is wrong
- Reduces perceived latency

**Potential Savings:** 10-30% if users cancel early; improved UX always

---

#### No Streaming

**File:** `codetests\llm_cost_assessment.py` (line 1378)
**Confidence:** ~ Low confidence

```
response = client.chat.completions.create(
```

**Issue:** API call without streaming enabled. For long responses, streaming improves user experience and allows early termination if the response isn't needed.

**Recommendation:**

Enable streaming for better UX and potential cost savings:

```python
# Streaming allows users to cancel early, saving tokens
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    stream=True  # Enable streaming
)

# Process streamed response
full_response = ""
for chunk in response:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        print(content, end="", flush=True)  # Show to user immediately
        full_response += content

        # Option: Allow early termination
        if user_cancelled():
            break  # Stop receiving (saves remaining tokens)
```

Benefits:
- Better UX (user sees response immediately)
- Can stop generation early if response is wrong
- Reduces perceived latency

**Potential Savings:** 10-30% if users cancel early; improved UX always

---

#### No Streaming

**File:** `codetests\llm_cost_assessment.py` (line 1392)
**Confidence:** ~ Low confidence

```
return client.chat.completions.create(...)
```

**Issue:** API call without streaming enabled. For long responses, streaming improves user experience and allows early termination if the response isn't needed.

**Recommendation:**

Enable streaming for better UX and potential cost savings:

```python
# Streaming allows users to cancel early, saving tokens
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    stream=True  # Enable streaming
)

# Process streamed response
full_response = ""
for chunk in response:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        print(content, end="", flush=True)  # Show to user immediately
        full_response += content

        # Option: Allow early termination
        if user_cancelled():
            break  # Stop receiving (saves remaining tokens)
```

Benefits:
- Better UX (user sees response immediately)
- Can stop generation early if response is wrong
- Reduces perceived latency

**Potential Savings:** 10-30% if users cancel early; improved UX always

---

#### Missing Error Handling

**File:** `codetests\llm_cost_assessment.py` (line 194)
**Confidence:** ? Medium confidence

```
response = client.chat.completions.create(
```

**Issue:** LLM API call without visible error handling. Failed requests still cost money, and retries without backoff can multiply costs.

**Recommendation:**

Add proper error handling with exponential backoff:

```python
import time
from openai import RateLimitError, APIError

def call_with_retry(func, max_retries: int = 3, base_delay: float = 1.0):
    '''Call API with exponential backoff.'''
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
        except APIError as e:
            if e.status_code >= 500:  # Server error, retry
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                else:
                    raise
            else:
                raise  # Client error, don't retry

# Usage
response = call_with_retry(
    lambda: client.chat.completions.create(...)
)
```

Or use tenacity library:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_llm(messages):
    return client.chat.completions.create(messages=messages)
```

**Potential Savings:** Prevents wasted costs from unhandled failures

---

#### Missing Error Handling

**File:** `codetests\llm_cost_assessment.py` (line 213)
**Confidence:** ? Medium confidence

```
r'ChatCompletion\.create\s*\(',
```

**Issue:** LLM API call without visible error handling. Failed requests still cost money, and retries without backoff can multiply costs.

**Recommendation:**

Add proper error handling with exponential backoff:

```python
import time
from openai import RateLimitError, APIError

def call_with_retry(func, max_retries: int = 3, base_delay: float = 1.0):
    '''Call API with exponential backoff.'''
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
        except APIError as e:
            if e.status_code >= 500:  # Server error, retry
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                else:
                    raise
            else:
                raise  # Client error, don't retry

# Usage
response = call_with_retry(
    lambda: client.chat.completions.create(...)
)
```

Or use tenacity library:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_llm(messages):
    return client.chat.completions.create(messages=messages)
```

**Potential Savings:** Prevents wasted costs from unhandled failures

---

#### Missing Error Handling

**File:** `codetests\llm_cost_assessment.py` (line 215)
**Confidence:** ? Medium confidence

```
r'openai\.ChatCompletion',
```

**Issue:** LLM API call without visible error handling. Failed requests still cost money, and retries without backoff can multiply costs.

**Recommendation:**

Add proper error handling with exponential backoff:

```python
import time
from openai import RateLimitError, APIError

def call_with_retry(func, max_retries: int = 3, base_delay: float = 1.0):
    '''Call API with exponential backoff.'''
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
        except APIError as e:
            if e.status_code >= 500:  # Server error, retry
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                else:
                    raise
            else:
                raise  # Client error, don't retry

# Usage
response = call_with_retry(
    lambda: client.chat.completions.create(...)
)
```

Or use tenacity library:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_llm(messages):
    return client.chat.completions.create(messages=messages)
```

**Potential Savings:** Prevents wasted costs from unhandled failures

---

#### Missing Error Handling

**File:** `codetests\llm_cost_assessment.py` (line 474)
**Confidence:** ? Medium confidence

```
r'ChatCompletion', r'client\.messages'
```

**Issue:** LLM API call without visible error handling. Failed requests still cost money, and retries without backoff can multiply costs.

**Recommendation:**

Add proper error handling with exponential backoff:

```python
import time
from openai import RateLimitError, APIError

def call_with_retry(func, max_retries: int = 3, base_delay: float = 1.0):
    '''Call API with exponential backoff.'''
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
        except APIError as e:
            if e.status_code >= 500:  # Server error, retry
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                else:
                    raise
            else:
                raise  # Client error, don't retry

# Usage
response = call_with_retry(
    lambda: client.chat.completions.create(...)
)
```

Or use tenacity library:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_llm(messages):
    return client.chat.completions.create(messages=messages)
```

**Potential Savings:** Prevents wasted costs from unhandled failures

---

#### Missing Error Handling

**File:** `codetests\llm_cost_assessment.py` (line 527)
**Confidence:** ? Medium confidence

```
result = client.chat.completions.create(...)
```

**Issue:** LLM API call without visible error handling. Failed requests still cost money, and retries without backoff can multiply costs.

**Recommendation:**

Add proper error handling with exponential backoff:

```python
import time
from openai import RateLimitError, APIError

def call_with_retry(func, max_retries: int = 3, base_delay: float = 1.0):
    '''Call API with exponential backoff.'''
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
        except APIError as e:
            if e.status_code >= 500:  # Server error, retry
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                else:
                    raise
            else:
                raise  # Client error, don't retry

# Usage
response = call_with_retry(
    lambda: client.chat.completions.create(...)
)
```

Or use tenacity library:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_llm(messages):
    return client.chat.completions.create(messages=messages)
```

**Potential Savings:** Prevents wasted costs from unhandled failures

---

#### Missing Error Handling

**File:** `codetests\llm_cost_assessment.py` (line 531)
**Confidence:** ? Medium confidence

```
result = client.chat.completions.create(
```

**Issue:** LLM API call without visible error handling. Failed requests still cost money, and retries without backoff can multiply costs.

**Recommendation:**

Add proper error handling with exponential backoff:

```python
import time
from openai import RateLimitError, APIError

def call_with_retry(func, max_retries: int = 3, base_delay: float = 1.0):
    '''Call API with exponential backoff.'''
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
        except APIError as e:
            if e.status_code >= 500:  # Server error, retry
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                else:
                    raise
            else:
                raise  # Client error, don't retry

# Usage
response = call_with_retry(
    lambda: client.chat.completions.create(...)
)
```

Or use tenacity library:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_llm(messages):
    return client.chat.completions.create(messages=messages)
```

**Potential Savings:** Prevents wasted costs from unhandled failures

---

#### Missing Error Handling

**File:** `codetests\llm_cost_assessment.py` (line 539)
**Confidence:** ? Medium confidence

```
return await async_client.chat.completions.create(...)
```

**Issue:** LLM API call without visible error handling. Failed requests still cost money, and retries without backoff can multiply costs.

**Recommendation:**

Add proper error handling with exponential backoff:

```python
import time
from openai import RateLimitError, APIError

def call_with_retry(func, max_retries: int = 3, base_delay: float = 1.0):
    '''Call API with exponential backoff.'''
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
        except APIError as e:
            if e.status_code >= 500:  # Server error, retry
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                else:
                    raise
            else:
                raise  # Client error, don't retry

# Usage
response = call_with_retry(
    lambda: client.chat.completions.create(...)
)
```

Or use tenacity library:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_llm(messages):
    return client.chat.completions.create(messages=messages)
```

**Potential Savings:** Prevents wasted costs from unhandled failures

---

#### Missing Error Handling

**File:** `codetests\llm_cost_assessment.py` (line 563)
**Confidence:** ? Medium confidence

```
r'ChatCompletion\.create', r'client\.messages\.create',
```

**Issue:** LLM API call without visible error handling. Failed requests still cost money, and retries without backoff can multiply costs.

**Recommendation:**

Add proper error handling with exponential backoff:

```python
import time
from openai import RateLimitError, APIError

def call_with_retry(func, max_retries: int = 3, base_delay: float = 1.0):
    '''Call API with exponential backoff.'''
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
        except APIError as e:
            if e.status_code >= 500:  # Server error, retry
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                else:
                    raise
            else:
                raise  # Client error, don't retry

# Usage
response = call_with_retry(
    lambda: client.chat.completions.create(...)
)
```

Or use tenacity library:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_llm(messages):
    return client.chat.completions.create(messages=messages)
```

**Potential Savings:** Prevents wasted costs from unhandled failures

---

#### Missing Error Handling

**File:** `codetests\llm_cost_assessment.py` (line 641)
**Confidence:** ? Medium confidence

```
result = client.chat.completions.create(
```

**Issue:** LLM API call without visible error handling. Failed requests still cost money, and retries without backoff can multiply costs.

**Recommendation:**

Add proper error handling with exponential backoff:

```python
import time
from openai import RateLimitError, APIError

def call_with_retry(func, max_retries: int = 3, base_delay: float = 1.0):
    '''Call API with exponential backoff.'''
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
        except APIError as e:
            if e.status_code >= 500:  # Server error, retry
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                else:
                    raise
            else:
                raise  # Client error, don't retry

# Usage
response = call_with_retry(
    lambda: client.chat.completions.create(...)
)
```

Or use tenacity library:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_llm(messages):
    return client.chat.completions.create(messages=messages)
```

**Potential Savings:** Prevents wasted costs from unhandled failures

---

#### Missing Error Handling

**File:** `codetests\llm_cost_assessment.py` (line 759)
**Confidence:** ? Medium confidence

```
API_PATTERNS = [r'\.create\s*\(', r'\.completions', r'ChatCompletion']
```

**Issue:** LLM API call without visible error handling. Failed requests still cost money, and retries without backoff can multiply costs.

**Recommendation:**

Add proper error handling with exponential backoff:

```python
import time
from openai import RateLimitError, APIError

def call_with_retry(func, max_retries: int = 3, base_delay: float = 1.0):
    '''Call API with exponential backoff.'''
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
        except APIError as e:
            if e.status_code >= 500:  # Server error, retry
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                else:
                    raise
            else:
                raise  # Client error, don't retry

# Usage
response = call_with_retry(
    lambda: client.chat.completions.create(...)
)
```

Or use tenacity library:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_llm(messages):
    return client.chat.completions.create(messages=messages)
```

**Potential Savings:** Prevents wasted costs from unhandled failures

---

#### Missing Error Handling

**File:** `codetests\llm_cost_assessment.py` (line 877)
**Confidence:** ? Medium confidence

```
response = client.chat.completions.create(
```

**Issue:** LLM API call without visible error handling. Failed requests still cost money, and retries without backoff can multiply costs.

**Recommendation:**

Add proper error handling with exponential backoff:

```python
import time
from openai import RateLimitError, APIError

def call_with_retry(func, max_retries: int = 3, base_delay: float = 1.0):
    '''Call API with exponential backoff.'''
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
        except APIError as e:
            if e.status_code >= 500:  # Server error, retry
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                else:
                    raise
            else:
                raise  # Client error, don't retry

# Usage
response = call_with_retry(
    lambda: client.chat.completions.create(...)
)
```

Or use tenacity library:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_llm(messages):
    return client.chat.completions.create(messages=messages)
```

**Potential Savings:** Prevents wasted costs from unhandled failures

---

#### Missing Error Handling

**File:** `codetests\llm_cost_assessment.py` (line 942)
**Confidence:** ? Medium confidence

```
response = client.embeddings.create(
```

**Issue:** LLM API call without visible error handling. Failed requests still cost money, and retries without backoff can multiply costs.

**Recommendation:**

Add proper error handling with exponential backoff:

```python
import time
from openai import RateLimitError, APIError

def call_with_retry(func, max_retries: int = 3, base_delay: float = 1.0):
    '''Call API with exponential backoff.'''
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
        except APIError as e:
            if e.status_code >= 500:  # Server error, retry
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                else:
                    raise
            else:
                raise  # Client error, don't retry

# Usage
response = call_with_retry(
    lambda: client.chat.completions.create(...)
)
```

Or use tenacity library:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_llm(messages):
    return client.chat.completions.create(messages=messages)
```

**Potential Savings:** Prevents wasted costs from unhandled failures

---

#### Missing Error Handling

**File:** `codetests\llm_cost_assessment.py` (line 1112)
**Confidence:** ? Medium confidence

```
r'ChatCompletion', r'chat\.completions',
```

**Issue:** LLM API call without visible error handling. Failed requests still cost money, and retries without backoff can multiply costs.

**Recommendation:**

Add proper error handling with exponential backoff:

```python
import time
from openai import RateLimitError, APIError

def call_with_retry(func, max_retries: int = 3, base_delay: float = 1.0):
    '''Call API with exponential backoff.'''
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
        except APIError as e:
            if e.status_code >= 500:  # Server error, retry
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                else:
                    raise
            else:
                raise  # Client error, don't retry

# Usage
response = call_with_retry(
    lambda: client.chat.completions.create(...)
)
```

Or use tenacity library:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_llm(messages):
    return client.chat.completions.create(messages=messages)
```

**Potential Savings:** Prevents wasted costs from unhandled failures

---

#### Missing Error Handling

**File:** `codetests\llm_cost_assessment.py` (line 1378)
**Confidence:** ? Medium confidence

```
response = client.chat.completions.create(
```

**Issue:** LLM API call without visible error handling. Failed requests still cost money, and retries without backoff can multiply costs.

**Recommendation:**

Add proper error handling with exponential backoff:

```python
import time
from openai import RateLimitError, APIError

def call_with_retry(func, max_retries: int = 3, base_delay: float = 1.0):
    '''Call API with exponential backoff.'''
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
        except APIError as e:
            if e.status_code >= 500:  # Server error, retry
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                else:
                    raise
            else:
                raise  # Client error, don't retry

# Usage
response = call_with_retry(
    lambda: client.chat.completions.create(...)
)
```

Or use tenacity library:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_llm(messages):
    return client.chat.completions.create(messages=messages)
```

**Potential Savings:** Prevents wasted costs from unhandled failures

---

#### Missing Error Handling

**File:** `codetests\llm_cost_assessment.py` (line 1392)
**Confidence:** ? Medium confidence

```
return client.chat.completions.create(...)
```

**Issue:** LLM API call without visible error handling. Failed requests still cost money, and retries without backoff can multiply costs.

**Recommendation:**

Add proper error handling with exponential backoff:

```python
import time
from openai import RateLimitError, APIError

def call_with_retry(func, max_retries: int = 3, base_delay: float = 1.0):
    '''Call API with exponential backoff.'''
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
        except APIError as e:
            if e.status_code >= 500:  # Server error, retry
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                else:
                    raise
            else:
                raise  # Client error, don't retry

# Usage
response = call_with_retry(
    lambda: client.chat.completions.create(...)
)
```

Or use tenacity library:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_llm(messages):
    return client.chat.completions.create(messages=messages)
```

**Potential Savings:** Prevents wasted costs from unhandled failures

---


## Quick Reference: Cost Optimization Patterns

### 1. Always Set Token Limits
```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    max_tokens=500  # Always set this!
)
```

### 2. Cache Responses
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def get_cached_response(prompt_hash):
    return client.chat.completions.create(...)
```

### 3. Manage Conversation History
```python
# Keep only last N messages
messages = messages[-10:]
```

### 4. Use Appropriate Models
```python
# Simple tasks: gpt-3.5-turbo ($0.0005/1K)
# Medium tasks: gpt-4o-mini ($0.00015/1K)
# Complex tasks: gpt-4o ($0.005/1K)
```

### 5. Count Tokens Before Sending
```python
import tiktoken
enc = tiktoken.encoding_for_model("gpt-4")
tokens = len(enc.encode(text))
```

---

*Report generated by ATLAS LLM Cost Assessment Tool v{result.assessment_version}*
