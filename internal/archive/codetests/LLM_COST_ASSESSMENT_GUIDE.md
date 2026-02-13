# LLM Cost Assessment Guide

This guide helps teams identify and fix common issues that cause excessive LLM/OpenAI token usage.

## Quick Start

### 1. Run the Assessment

```bash
# Analyze your project
python llm_cost_assessment.py /path/to/your/project

# Generate markdown report
python llm_cost_assessment.py /path/to/your/project --output report.md

# Get JSON output for programmatic processing
python llm_cost_assessment.py /path/to/your/project --json > results.json
```

### 2. Understand the Severity Levels

| Severity | Impact | Action Required |
|----------|--------|-----------------|
| 🔴 Critical | 50-90% cost increase | Fix immediately |
| 🟠 High | 20-50% cost increase | Fix this week |
| 🟡 Medium | 10-20% cost increase | Plan to fix |
| 🟢 Low | 5-10% cost increase | Nice to have |

---

## Common Issues and Fixes

### 1. 🔴 Full Conversation History (Critical)

**Problem:** Sending the entire chat history with every request.

```python
# ❌ BAD: Token count grows with every message
messages = conversation_history  # Could be thousands of tokens!
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages
)
```

**Solution:**

```python
# ✅ GOOD: Limit history and summarize
def manage_conversation(messages: list, max_messages: int = 10):
    if len(messages) <= max_messages:
        return messages

    # Keep system message + summarize old + keep recent
    system_msg = [m for m in messages if m["role"] == "system"]
    old_messages = [m for m in messages if m["role"] != "system"][:-max_messages]
    recent_messages = [m for m in messages if m["role"] != "system"][-max_messages:]

    # Summarize old context
    summary = summarize_messages(old_messages)

    return system_msg + [
        {"role": "system", "content": f"Previous context: {summary}"}
    ] + recent_messages
```

**Savings:** 60-90% for long conversations

---

### 2. 🔴 Large System Prompts Without Caching (Critical)

**Problem:** Sending a 2000+ token system prompt with every request.

```python
# ❌ BAD: Large prompt sent every time
SYSTEM_PROMPT = """
You are an expert analyst. Here are 50 rules you must follow:
1. Always be accurate...
2. Consider all perspectives...
... (2000 more tokens)
"""

for item in items:  # 100 items = 200,000+ tokens just for system prompts!
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze: {item}"}
        ]
    )
```

**Solution:**

```python
# ✅ GOOD: Use prompt caching (OpenAI supports this automatically for identical prompts)
# Also batch items together
def analyze_batch(items: list, batch_size: int = 10):
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        batch_prompt = "Analyze each item:\n" + "\n".join(f"- {item}" for item in batch)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},  # Cached after first call
                {"role": "user", "content": batch_prompt}
            ]
        )
        results.extend(parse_batch_response(response))
    return results
```

**Savings:** 40-60% with caching, 80-95% with batching

---

### 3. 🟠 No max_tokens Limit (High)

**Problem:** Model generates as many tokens as it wants.

```python
# ❌ BAD: No limit on response length
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages
)
# Model might generate 4000 tokens when you only need 100!
```

**Solution:**

```python
# ✅ GOOD: Set appropriate limits
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    max_tokens=500,  # Limit based on actual need
    temperature=0.7
)
```

**Savings:** 20-40% typical

---

### 4. 🟠 No Response Caching (High)

**Problem:** Same questions get sent to the API multiple times.

```python
# ❌ BAD: No caching - same question = same cost every time
def get_answer(question: str):
    return client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": question}]
    )
```

**Solution:**

```python
# ✅ GOOD: Cache responses
from functools import lru_cache
import hashlib

# Simple in-memory cache
@lru_cache(maxsize=1000)
def get_answer_cached(question_hash: str, question: str):
    return client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": question}]
    )

def get_answer(question: str):
    question_hash = hashlib.md5(question.encode()).hexdigest()
    return get_answer_cached(question_hash, question)

# For production: use Redis
import redis
import json

redis_client = redis.Redis()
CACHE_TTL = 3600  # 1 hour

def get_answer_redis(question: str):
    cache_key = f"llm:{hashlib.md5(question.encode()).hexdigest()}"

    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": question}]
    )

    redis_client.setex(cache_key, CACHE_TTL, json.dumps(response.model_dump()))
    return response
```

**Savings:** 50-90% for repeated queries

---

### 5. 🟠 Large Files in Prompts (High)

**Problem:** Embedding entire files in prompts.

```python
# ❌ BAD: Send entire file (could be 100K+ tokens!)
with open("large_document.txt") as f:
    content = f.read()

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": f"Summarize this:\n{content}"}
    ]
)
```

**Solution:**

```python
# ✅ GOOD: Chunk and process incrementally
def chunk_text(text: str, chunk_size: int = 3000) -> list:
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0

    for word in words:
        if current_size + len(word) > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_size = len(word)
        else:
            current_chunk.append(word)
            current_size += len(word) + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def summarize_large_document(file_path: str):
    with open(file_path) as f:
        content = f.read()

    chunks = chunk_text(content)
    summaries = []

    for chunk in chunks:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Cheaper for summarization
            messages=[{"role": "user", "content": f"Summarize:\n{chunk}"}],
            max_tokens=200
        )
        summaries.append(response.choices[0].message.content)

    # Final summary of summaries
    final_response = client.chat.completions.create(
        model="gpt-4",  # Better model for final synthesis
        messages=[{"role": "user", "content": f"Combine these summaries:\n{chr(10).join(summaries)}"}],
        max_tokens=500
    )
    return final_response.choices[0].message.content
```

**Savings:** 70-95% for large documents

---

### 6. 🟡 Using Expensive Models for Simple Tasks (Medium)

**Problem:** Using GPT-4 for everything.

```python
# ❌ BAD: GPT-4 for simple classification
def classify_sentiment(text: str):
    response = client.chat.completions.create(
        model="gpt-4",  # $0.03/1K input, $0.06/1K output
        messages=[{"role": "user", "content": f"Is this positive or negative: {text}"}]
    )
```

**Solution:**

```python
# ✅ GOOD: Right model for the job
MODEL_TIERS = {
    "simple": "gpt-3.5-turbo",     # $0.0005/1K - Classification, extraction, formatting
    "medium": "gpt-4o-mini",        # $0.00015/1K - General tasks, Q&A
    "complex": "gpt-4o",            # $0.005/1K - Complex reasoning, analysis
}

def classify_sentiment(text: str):
    response = client.chat.completions.create(
        model=MODEL_TIERS["simple"],  # 60x cheaper!
        messages=[{"role": "user", "content": f"Is this positive or negative: {text}"}]
    )

def analyze_complex_data(data: dict):
    response = client.chat.completions.create(
        model=MODEL_TIERS["complex"],  # Use expensive model only when needed
        messages=[{"role": "user", "content": f"Analyze trends: {data}"}]
    )
```

**Savings:** 50-95% per request depending on task

---

### 7. 🟡 No Token Counting (Medium)

**Problem:** Can't predict costs or prevent context overflow.

**Solution:**

```python
import tiktoken

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens for a given text."""
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

def estimate_cost(messages: list, model: str = "gpt-4") -> float:
    """Estimate cost before making API call."""
    PRICES = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    }

    total_tokens = sum(count_tokens(m["content"]) for m in messages)
    price = PRICES.get(model, PRICES["gpt-4"])

    input_cost = (total_tokens / 1000) * price["input"]
    # Estimate output at 50% of input
    output_cost = (total_tokens * 0.5 / 1000) * price["output"]

    return input_cost + output_cost

# Usage
messages = [...]
estimated = estimate_cost(messages, "gpt-4")
print(f"Estimated cost: ${estimated:.4f}")

if estimated > 1.0:  # Warning threshold
    print("Warning: High cost request!")
```

---

## Cost Monitoring Dashboard

Add this to track your LLM costs:

```python
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class LLMUsage:
    timestamp: datetime
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    endpoint: str

class CostTracker:
    def __init__(self, log_file: str = "llm_costs.jsonl"):
        self.log_file = log_file
        self.session_cost = 0.0

    def log_usage(self, response, model: str, endpoint: str):
        usage = response.usage
        cost = self._calculate_cost(model, usage.prompt_tokens, usage.completion_tokens)

        entry = LLMUsage(
            timestamp=datetime.now(),
            model=model,
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            cost=cost,
            endpoint=endpoint
        )

        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry.__dict__, default=str) + "\n")

        self.session_cost += cost
        return cost

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        prices = {
            "gpt-4": (0.03, 0.06),
            "gpt-4o": (0.005, 0.015),
            "gpt-4o-mini": (0.00015, 0.0006),
            "gpt-3.5-turbo": (0.0005, 0.0015),
        }
        input_price, output_price = prices.get(model, (0.01, 0.03))
        return (input_tokens * input_price + output_tokens * output_price) / 1000

# Usage
tracker = CostTracker()

response = client.chat.completions.create(...)
cost = tracker.log_usage(response, "gpt-4", "/api/analyze")
print(f"This request cost: ${cost:.4f}")
print(f"Session total: ${tracker.session_cost:.4f}")
```

---

## Checklist Before Deployment

- [ ] All API calls have `max_tokens` set
- [ ] Response caching is implemented
- [ ] Conversation history is managed (summarized/truncated)
- [ ] Large files are chunked before processing
- [ ] Token counting is in place
- [ ] Appropriate models selected for each task
- [ ] Cost monitoring/alerting is configured
- [ ] Rate limiting is implemented

---

## Need Help?

If you find issues specific to your codebase that aren't covered here, the assessment tool generates specific recommendations for each finding. Run:

```bash
python llm_cost_assessment.py /your/project --output detailed_report.md
```

And review the "Detailed Findings" section for file-specific recommendations.
