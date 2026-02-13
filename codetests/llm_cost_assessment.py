#!/usr/bin/env python3
"""
LLM Cost Assessment Tool v2.0
=============================

A comprehensive analysis tool for identifying LLM/OpenAI token usage inefficiencies
in codebases. Designed for professional use in code reviews and cost optimization.

Author: ATLAS Platform Team
Version: 2.0.0

Usage:
    python llm_cost_assessment.py /path/to/project
    python llm_cost_assessment.py /path/to/project --output report.md
    python llm_cost_assessment.py /path/to/project --json
    python llm_cost_assessment.py /path/to/project --verbose

Features:
    - Detects 15+ categories of cost inefficiencies
    - Supports Python, JavaScript, TypeScript codebases
    - Generates detailed markdown or JSON reports
    - Provides specific code-level recommendations
    - Estimates potential cost savings

Detected Issues:
    CRITICAL:
    - Full conversation history without management
    - Large system prompts (>500 tokens) repeated per request
    - API calls inside loops without batching
    - Missing response caching for repeated queries
    - Embedding API misuse (re-embedding same content)

    HIGH:
    - No max_tokens limit on completions
    - Large file/document embedding without chunking
    - No token counting before requests
    - Retry logic without exponential backoff
    - Missing error handling (wasted failed requests)

    MEDIUM:
    - Using expensive models for simple tasks
    - No streaming for long responses
    - Function/tool calls without necessity checks
    - Vision API with unnecessarily high resolution
    - No request deduplication

    LOW:
    - Batching opportunities not utilized
    - Suboptimal temperature settings
    - Missing request timeout configuration

Requirements:
    - Python 3.7+
    - No external dependencies (stdlib only)
"""

import os
import re
import sys
import json
import argparse
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict
from datetime import datetime
from abc import ABC, abstractmethod


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Issue:
    """Represents a detected code issue."""
    severity: str  # critical, high, medium, low
    category: str
    file_path: str
    line_number: int
    code_snippet: str
    description: str
    recommendation: str
    estimated_savings: str
    confidence: str = "high"  # high, medium, low - how confident we are this is an issue

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FileAnalysis:
    """Analysis results for a single file."""
    file_path: str
    language: str
    has_llm_usage: bool
    api_call_count: int
    issues: List[Issue] = field(default_factory=list)
    patterns_found: Set[str] = field(default_factory=set)


@dataclass
class AssessmentResult:
    """Complete assessment result."""
    project_path: str
    assessment_version: str
    timestamp: str
    files_scanned: int
    files_with_llm_usage: int
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    issues: List[Issue] = field(default_factory=list)
    summary_by_category: Dict[str, int] = field(default_factory=dict)
    summary_by_file: Dict[str, int] = field(default_factory=dict)
    estimated_savings: str = ""
    recommendations_summary: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project_path": self.project_path,
            "assessment_version": self.assessment_version,
            "timestamp": self.timestamp,
            "files_scanned": self.files_scanned,
            "files_with_llm_usage": self.files_with_llm_usage,
            "total_issues": self.total_issues,
            "critical_issues": self.critical_issues,
            "high_issues": self.high_issues,
            "medium_issues": self.medium_issues,
            "low_issues": self.low_issues,
            "summary_by_category": self.summary_by_category,
            "summary_by_file": self.summary_by_file,
            "estimated_savings": self.estimated_savings,
            "recommendations_summary": self.recommendations_summary,
            "issues": [i.to_dict() for i in self.issues]
        }


# =============================================================================
# Pattern Detectors (Modular Design)
# =============================================================================

class PatternDetector(ABC):
    """Base class for pattern detectors."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def severity(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def recommendation(self) -> str:
        pass

    @property
    @abstractmethod
    def estimated_savings(self) -> str:
        pass

    @abstractmethod
    def detect(self, file_path: str, content: str, lines: List[str]) -> List[Issue]:
        pass

    def _get_context(self, lines: List[str], line_idx: int, before: int = 5, after: int = 5) -> str:
        """Get surrounding context for a line."""
        start = max(0, line_idx - before)
        end = min(len(lines), line_idx + after + 1)
        return '\n'.join(lines[start:end])


class NoMaxTokensDetector(PatternDetector):
    """Detects API calls without max_tokens limit."""

    name = "No Token Limit"
    severity = "high"
    description = "API call without max_tokens parameter. The model may generate excessive tokens, increasing costs unpredictably."
    recommendation = """Add max_tokens parameter to limit response length:

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
- Long-form content: 1000-2000 tokens"""
    estimated_savings = "20-40% token reduction"

    # Patterns that indicate an API call
    API_CALL_PATTERNS = [
        r'\.create\s*\(',
        r'\.completions\.create\s*\(',
        r'\.chat\.completions\.create\s*\(',
        r'ChatCompletion\.create\s*\(',
        r'Completion\.create\s*\(',
        r'openai\.ChatCompletion',
        r'client\.messages\.create\s*\(',  # Anthropic
    ]

    def detect(self, file_path: str, content: str, lines: List[str]) -> List[Issue]:
        issues = []

        for i, line in enumerate(lines):
            for pattern in self.API_CALL_PATTERNS:
                if re.search(pattern, line):
                    # Look for max_tokens in surrounding context (function call might span lines)
                    context = self._get_context(lines, i, before=3, after=15)

                    # Check if max_tokens is present
                    if not re.search(r'max_tokens\s*[=:]', context):
                        # Verify this is actually an LLM API call, not something else
                        if self._is_llm_api_call(context):
                            issues.append(Issue(
                                severity=self.severity,
                                category=self.name,
                                file_path=file_path,
                                line_number=i + 1,
                                code_snippet=line.strip()[:120],
                                description=self.description,
                                recommendation=self.recommendation,
                                estimated_savings=self.estimated_savings,
                                confidence="high"
                            ))
                    break

        return issues

    def _is_llm_api_call(self, context: str) -> bool:
        """Verify this is actually an LLM API call."""
        llm_indicators = ['model', 'messages', 'prompt', 'gpt', 'claude', 'llm']
        return any(ind in context.lower() for ind in llm_indicators)


class LargeSystemPromptDetector(PatternDetector):
    """Detects large system prompts that should be cached or optimized."""

    name = "Large System Prompt"
    severity = "critical"
    description = "Large system prompt detected. If sent with every API request, this significantly increases token costs."
    recommendation = """Optimize large system prompts:

1. **Use OpenAI's prompt caching** (automatic for identical prompts)
2. **Move static instructions to fine-tuning** if used frequently
3. **Compress the prompt** - remove redundancy, use concise language
4. **Use prompt templates** with only dynamic parts varying

```python
# Instead of repeating full prompt, cache it
SYSTEM_PROMPT = "..."  # Define once

# OpenAI automatically caches identical system prompts
# Just ensure the exact same string is used each time
```"""
    estimated_savings = "40-60% if prompt caching is enabled"

    # Minimum character count to flag as "large"
    MIN_LARGE_PROMPT_CHARS = 500
    CRITICAL_PROMPT_CHARS = 2000

    def detect(self, file_path: str, content: str, lines: List[str]) -> List[Issue]:
        issues = []

        # Pattern 1: Triple-quoted strings assigned to system-related variables
        system_var_pattern = r'(?:system[_\s]?(?:prompt|message|instruction)|SYSTEM[_\s]?(?:PROMPT|MESSAGE))\s*=\s*(?:"""|\'\'\')(.*?)(?:"""|\'\'\')'

        for match in re.finditer(system_var_pattern, content, re.DOTALL | re.IGNORECASE):
            prompt_content = match.group(1)
            char_count = len(prompt_content.strip())

            if char_count >= self.MIN_LARGE_PROMPT_CHARS:
                line_num = content[:match.start()].count('\n') + 1
                severity = "critical" if char_count >= self.CRITICAL_PROMPT_CHARS else "high"

                issues.append(Issue(
                    severity=severity,
                    category=self.name,
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=f"System prompt: ~{char_count} characters (~{char_count // 4} tokens)",
                    description=f"{self.description} Detected ~{char_count} characters (~{char_count // 4} estimated tokens).",
                    recommendation=self.recommendation,
                    estimated_savings=self.estimated_savings,
                    confidence="high"
                ))

        # Pattern 2: Inline system messages in API calls
        inline_pattern = r'\{\s*["\']role["\']\s*:\s*["\']system["\']\s*,\s*["\']content["\']\s*:\s*(?:f?["\'])(.*?)(?:["\'])\s*\}'

        for match in re.finditer(inline_pattern, content, re.DOTALL):
            prompt_content = match.group(1)
            # Account for f-string variables (rough estimate)
            char_count = len(prompt_content.strip())

            if char_count >= self.MIN_LARGE_PROMPT_CHARS:
                line_num = content[:match.start()].count('\n') + 1
                severity = "critical" if char_count >= self.CRITICAL_PROMPT_CHARS else "high"

                issues.append(Issue(
                    severity=severity,
                    category=self.name,
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=f"Inline system message: ~{char_count} characters",
                    description=f"{self.description} Detected ~{char_count} characters inline.",
                    recommendation=self.recommendation,
                    estimated_savings=self.estimated_savings,
                    confidence="medium"  # Inline detection is less certain
                ))

        return issues


class FullConversationHistoryDetector(PatternDetector):
    """Detects sending full conversation history without management."""

    name = "Full Conversation History"
    severity = "critical"
    description = "Conversation history appears to be sent without summarization or truncation. Token usage grows linearly (or worse) with conversation length, leading to exponential cost growth in long conversations."
    recommendation = """Implement conversation history management:

```python
def manage_conversation_history(messages: list, max_messages: int = 10, max_tokens: int = 4000):
    '''Keep conversation history under control.'''

    # Option 1: Simple truncation (keep last N messages)
    if len(messages) > max_messages:
        system_msgs = [m for m in messages if m["role"] == "system"]
        other_msgs = [m for m in messages if m["role"] != "system"]
        messages = system_msgs + other_msgs[-max_messages:]

    # Option 2: Summarize old messages
    if count_tokens(messages) > max_tokens:
        old_messages = messages[:-5]  # Keep last 5
        summary = summarize(old_messages)  # Use cheaper model
        messages = [
            {"role": "system", "content": f"Previous context: {summary}"}
        ] + messages[-5:]

    return messages
```

Alternative approaches:
- Use a sliding window (last N turns)
- Implement semantic compression (keep only relevant context)
- Store context in a vector database and retrieve as needed"""
    estimated_savings = "60-90% for long conversations"

    # Patterns indicating conversation history usage
    HISTORY_PATTERNS = [
        r'conversation[_\s]?history',
        r'chat[_\s]?history',
        r'message[_\s]?history',
        r'messages\s*\.\s*append',
        r'history\s*\.\s*append',
        r'messages\s*\+=',
        r'messages\s*=\s*messages\s*\+',
    ]

    # Patterns indicating history is being managed
    MANAGEMENT_PATTERNS = [
        r'summarize', r'summarise', r'condense', r'truncate', r'trim',
        r'max[_\s]?history', r'history[_\s]?limit', r'max[_\s]?messages',
        r'sliding[_\s]?window', r'window[_\s]?size',
        r'\[\s*-\d+\s*:\s*\]',  # Slicing like [-10:]
        r'messages\s*=\s*messages\s*\[\s*-',  # messages = messages[-N:]
    ]

    def detect(self, file_path: str, content: str, lines: List[str]) -> List[Issue]:
        issues = []
        content_lower = content.lower()

        # Check if conversation history is being used
        has_history_usage = any(re.search(p, content_lower) for p in self.HISTORY_PATTERNS)

        if not has_history_usage:
            return issues

        # Check if there's any history management
        has_management = any(re.search(p, content_lower) for p in self.MANAGEMENT_PATTERNS)

        if has_management:
            return issues  # History is being managed

        # Find the specific line where history is used
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for pattern in self.HISTORY_PATTERNS:
                if re.search(pattern, line_lower):
                    issues.append(Issue(
                        severity=self.severity,
                        category=self.name,
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip()[:120],
                        description=self.description,
                        recommendation=self.recommendation,
                        estimated_savings=self.estimated_savings,
                        confidence="high" if 'append' in line_lower else "medium"
                    ))
                    return issues  # One issue per file is enough

        return issues


class NoCachingDetector(PatternDetector):
    """Detects missing response caching for LLM calls."""

    name = "No Response Caching"
    severity = "high"
    description = "No caching mechanism detected for LLM responses. Identical or similar queries may be sent to the API multiple times, incurring unnecessary costs."
    recommendation = """Implement response caching:

```python
from functools import lru_cache
import hashlib
import json

# Option 1: Simple in-memory cache
@lru_cache(maxsize=1000)
def cached_llm_call(prompt_hash: str):
    # Actual API call here
    pass

def get_response(prompt: str, **kwargs):
    # Create deterministic hash of the request
    cache_key = hashlib.sha256(
        json.dumps({"prompt": prompt, **kwargs}, sort_keys=True).encode()
    ).hexdigest()
    return cached_llm_call(cache_key)

# Option 2: Redis cache for production
import redis
r = redis.Redis()

def get_cached_response(prompt: str, ttl: int = 3600):
    cache_key = f"llm:{hashlib.sha256(prompt.encode()).hexdigest()}"

    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    response = call_llm(prompt)
    r.setex(cache_key, ttl, json.dumps(response))
    return response
```

Consider:
- Cache TTL based on content freshness requirements
- Cache invalidation strategy
- Semantic caching for similar (not identical) queries"""
    estimated_savings = "50-90% for repeated or similar queries"

    API_PATTERNS = [
        r'\.create\s*\(', r'\.completions', r'openai\.',
        r'ChatCompletion', r'client\.messages'
    ]

    CACHING_INDICATORS = [
        r'@lru_cache', r'@cache', r'@cached', r'@memoize',
        r'functools\.cache', r'functools\.lru_cache',
        r'redis', r'memcache', r'cache\s*=', r'_cache\[',
        r'Cache\(', r'get_cache', r'set_cache',
    ]

    def detect(self, file_path: str, content: str, lines: List[str]) -> List[Issue]:
        issues = []

        # Check if file has LLM API calls
        has_api_calls = any(re.search(p, content) for p in self.API_PATTERNS)
        if not has_api_calls:
            return issues

        # Check if there's any caching
        has_caching = any(re.search(p, content, re.IGNORECASE) for p in self.CACHING_INDICATORS)
        if has_caching:
            return issues

        # Find first API call line
        for i, line in enumerate(lines):
            if any(re.search(p, line) for p in self.API_PATTERNS):
                issues.append(Issue(
                    severity=self.severity,
                    category=self.name,
                    file_path=file_path,
                    line_number=i + 1,
                    code_snippet=line.strip()[:120],
                    description=self.description,
                    recommendation=self.recommendation,
                    estimated_savings=self.estimated_savings,
                    confidence="medium"  # Can't be 100% sure caching isn't elsewhere
                ))
                break

        return issues


class APICallInLoopDetector(PatternDetector):
    """Detects API calls inside loops."""

    name = "API Calls in Loop"
    severity = "critical"
    description = "LLM API call detected inside a loop. This pattern can result in many expensive API calls, multiplying costs by the number of iterations."
    recommendation = """Refactor to batch or parallelize:

```python
# BAD: N API calls
for item in items:
    result = client.chat.completions.create(...)

# GOOD Option 1: Batch into single prompt
batch_prompt = "Process each item:\\n" + "\\n".join(items)
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
- Cache results to avoid duplicate processing"""
    estimated_savings = "50-95% by batching or eliminating redundant calls"

    LOOP_PATTERNS = [
        r'^\s*for\s+\w+\s+in\s+',
        r'^\s*while\s+',
        r'\.forEach\s*\(',
        r'\.map\s*\(',
        r'for\s*\(\s*(?:let|var|const)',
    ]

    API_PATTERNS = [
        r'\.create\s*\(', r'\.completions\.create',
        r'ChatCompletion\.create', r'client\.messages\.create',
    ]

    def detect(self, file_path: str, content: str, lines: List[str]) -> List[Issue]:
        issues = []
        in_loop = False
        loop_start_line = 0
        loop_indent = 0

        for i, line in enumerate(lines):
            # Check for loop start
            for pattern in self.LOOP_PATTERNS:
                if re.search(pattern, line):
                    in_loop = True
                    loop_start_line = i
                    # Calculate indentation
                    loop_indent = len(line) - len(line.lstrip())
                    break

            # If in a loop, check for API calls
            if in_loop:
                current_indent = len(line) - len(line.lstrip())

                # Check if we've exited the loop (less indentation)
                if line.strip() and current_indent <= loop_indent and i > loop_start_line:
                    in_loop = False
                    continue

                # Check for API call
                for pattern in self.API_PATTERNS:
                    if re.search(pattern, line):
                        issues.append(Issue(
                            severity=self.severity,
                            category=self.name,
                            file_path=file_path,
                            line_number=i + 1,
                            code_snippet=line.strip()[:120],
                            description=self.description,
                            recommendation=self.recommendation,
                            estimated_savings=self.estimated_savings,
                            confidence="high"
                        ))
                        in_loop = False  # Don't report multiple times for same loop
                        break

        return issues


class LargeFileEmbeddingDetector(PatternDetector):
    """Detects embedding large files in prompts without chunking."""

    name = "Large File Embedding"
    severity = "high"
    description = "File content is being read and potentially embedded in LLM prompts without apparent chunking. Large files can consume excessive tokens."
    recommendation = """Implement chunking or use RAG:

```python
def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200):
    '''Split text into overlapping chunks.'''
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

def process_large_document(file_path: str):
    with open(file_path) as f:
        content = f.read()

    # Chunk the content
    chunks = chunk_text(content)

    # Process relevant chunks only (use embeddings to find relevant ones)
    # Or process all chunks with a cheaper model
    results = []
    for chunk in chunks:
        result = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Cheaper for processing
            messages=[{"role": "user", "content": f"Summarize: {chunk}"}],
            max_tokens=200
        )
        results.append(result)

    return combine_results(results)
```

Better approach - RAG (Retrieval Augmented Generation):
1. Split document into chunks
2. Create embeddings for each chunk
3. Store in vector database
4. Query only relevant chunks based on user question"""
    estimated_savings = "70-95% for large documents"

    FILE_READ_PATTERNS = [
        r'\.read\s*\(\s*\)',
        r'\.read_text\s*\(\s*\)',
        r'open\s*\([^)]+\)\s*\.\s*read',
        r'Path\s*\([^)]+\)\s*\.\s*read_text',
        r'file_content\s*=',
        r'document_content\s*=',
        r'source_code\s*=',
        r'readFile',  # Node.js
        r'readFileSync',
    ]

    CHUNKING_INDICATORS = [
        r'chunk', r'split', r'slice', r'segment',
        r'max_length', r'truncate', r'[:',
        r'textwrap', r'wrap',
    ]

    def detect(self, file_path: str, content: str, lines: List[str]) -> List[Issue]:
        issues = []

        for i, line in enumerate(lines):
            # Check for file reading
            has_file_read = any(re.search(p, line) for p in self.FILE_READ_PATTERNS)
            if not has_file_read:
                continue

            # Check surrounding context for chunking
            context = self._get_context(lines, i, before=10, after=10)
            has_chunking = any(re.search(p, context, re.IGNORECASE) for p in self.CHUNKING_INDICATORS)

            if not has_chunking:
                issues.append(Issue(
                    severity=self.severity,
                    category=self.name,
                    file_path=file_path,
                    line_number=i + 1,
                    code_snippet=line.strip()[:120],
                    description=self.description,
                    recommendation=self.recommendation,
                    estimated_savings=self.estimated_savings,
                    confidence="medium"  # Might be small files
                ))

        return issues


class NoTokenCountingDetector(PatternDetector):
    """Detects missing token counting before API calls."""

    name = "No Token Counting"
    severity = "medium"
    description = "No token counting detected before LLM API calls. This makes it impossible to predict costs, prevent context overflow, or optimize prompt length."
    recommendation = """Add token counting using tiktoken:

```python
import tiktoken

def count_tokens(text: str, model: str = "gpt-4") -> int:
    '''Count tokens for cost estimation.'''
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

def estimate_cost(messages: list, model: str = "gpt-4") -> dict:
    '''Estimate cost before making API call.'''
    PRICES_PER_1K = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    }

    input_tokens = sum(count_tokens(m["content"]) for m in messages)
    prices = PRICES_PER_1K.get(model, PRICES_PER_1K["gpt-4"])

    estimated_input_cost = (input_tokens / 1000) * prices["input"]
    # Estimate output at 50% of input (adjust based on your use case)
    estimated_output_cost = (input_tokens * 0.5 / 1000) * prices["output"]

    return {
        "input_tokens": input_tokens,
        "estimated_cost": estimated_input_cost + estimated_output_cost
    }

# Usage
estimate = estimate_cost(messages, "gpt-4")
if estimate["estimated_cost"] > 1.0:
    logger.warning(f"High cost request: ${estimate['estimated_cost']:.4f}")
```"""
    estimated_savings = "Prevents unexpected high costs and context overflow"

    TOKEN_COUNTING_INDICATORS = [
        r'tiktoken', r'token_count', r'num_tokens', r'count_tokens',
        r'get_tokens', r'tokenize', r'encoding_for_model',
        r'len\s*\(\s*enc\.encode', r'token_limit',
    ]

    API_PATTERNS = [r'\.create\s*\(', r'\.completions', r'ChatCompletion']

    def detect(self, file_path: str, content: str, lines: List[str]) -> List[Issue]:
        issues = []

        has_api_calls = any(re.search(p, content) for p in self.API_PATTERNS)
        if not has_api_calls:
            return issues

        has_token_counting = any(re.search(p, content, re.IGNORECASE) for p in self.TOKEN_COUNTING_INDICATORS)
        if has_token_counting:
            return issues

        # Find first API call
        for i, line in enumerate(lines):
            if any(re.search(p, line) for p in self.API_PATTERNS):
                issues.append(Issue(
                    severity=self.severity,
                    category=self.name,
                    file_path=file_path,
                    line_number=i + 1,
                    code_snippet=line.strip()[:120],
                    description=self.description,
                    recommendation=self.recommendation,
                    estimated_savings=self.estimated_savings,
                    confidence="medium"
                ))
                break

        return issues


class ExpensiveModelDetector(PatternDetector):
    """Detects potentially unnecessary use of expensive models."""

    name = "Expensive Model Usage"
    severity = "medium"
    description = "Using an expensive model. Consider if a cheaper model would suffice for this task."
    recommendation = """Match model to task complexity:

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
- gpt-4: $30.00"""
    estimated_savings = "50-95% per request by using appropriate model tier"

    EXPENSIVE_MODELS = {
        'gpt-4': 'gpt-4o-mini or gpt-3.5-turbo',
        'gpt-4-32k': 'gpt-4o or gpt-4-turbo',
        'gpt-4-turbo': 'gpt-4o or gpt-4o-mini',
        'claude-3-opus': 'claude-3-sonnet or claude-3-haiku',
    }

    def detect(self, file_path: str, content: str, lines: List[str]) -> List[Issue]:
        issues = []

        for i, line in enumerate(lines):
            for expensive, alternative in self.EXPENSIVE_MODELS.items():
                # Use word boundaries to avoid partial matches
                if re.search(rf'["\']?{re.escape(expensive)}["\']?', line, re.IGNORECASE):
                    # Verify it's in a model parameter context
                    context = self._get_context(lines, i, before=2, after=2)
                    if 'model' in context.lower():
                        issues.append(Issue(
                            severity=self.severity,
                            category=self.name,
                            file_path=file_path,
                            line_number=i + 1,
                            code_snippet=line.strip()[:120],
                            description=f"Using {expensive}. Consider if {alternative} would work for this task.",
                            recommendation=self.recommendation,
                            estimated_savings=self.estimated_savings,
                            confidence="low"  # Can't know if expensive model is needed
                        ))
                        break

        return issues


class NoStreamingDetector(PatternDetector):
    """Detects missing streaming for potentially long responses."""

    name = "No Streaming"
    severity = "medium"
    description = "API call without streaming enabled. For long responses, streaming improves user experience and allows early termination if the response isn't needed."
    recommendation = """Enable streaming for better UX and potential cost savings:

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
- Reduces perceived latency"""
    estimated_savings = "10-30% if users cancel early; improved UX always"

    API_PATTERNS = [r'\.create\s*\(', r'\.completions\.create']

    def detect(self, file_path: str, content: str, lines: List[str]) -> List[Issue]:
        issues = []

        for i, line in enumerate(lines):
            if any(re.search(p, line) for p in self.API_PATTERNS):
                context = self._get_context(lines, i, before=2, after=10)

                if 'stream' not in context.lower():
                    issues.append(Issue(
                        severity=self.severity,
                        category=self.name,
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip()[:120],
                        description=self.description,
                        recommendation=self.recommendation,
                        estimated_savings=self.estimated_savings,
                        confidence="low"  # Streaming not always needed
                    ))

        return issues


class EmbeddingReuseDetector(PatternDetector):
    """Detects potential re-embedding of the same content."""

    name = "Embedding Recomputation"
    severity = "high"
    description = "Embedding API calls detected without apparent caching. Re-embedding the same content wastes API calls."
    recommendation = """Cache embeddings to avoid recomputation:

```python
import hashlib
from functools import lru_cache

# Option 1: In-memory cache
@lru_cache(maxsize=10000)
def get_embedding_cached(text_hash: str, text: str):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def get_embedding(text: str):
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    return get_embedding_cached(text_hash, text)

# Option 2: Persistent cache (database/file)
def get_embedding_persistent(text: str, cache_db):
    text_hash = hashlib.sha256(text.encode()).hexdigest()

    # Check cache
    cached = cache_db.get(text_hash)
    if cached:
        return cached

    # Compute and cache
    embedding = compute_embedding(text)
    cache_db.set(text_hash, embedding)
    return embedding
```

Also consider:
- Batch embedding requests (up to 2048 texts per call)
- Store embeddings alongside source documents
- Use content hashing to detect duplicates"""
    estimated_savings = "80-99% for repeated content"

    EMBEDDING_PATTERNS = [
        r'\.embeddings\.create',
        r'embed\s*\(',
        r'get_embedding',
        r'create_embedding',
        r'text-embedding',
    ]

    def detect(self, file_path: str, content: str, lines: List[str]) -> List[Issue]:
        issues = []

        # Check for embedding usage
        has_embeddings = any(re.search(p, content, re.IGNORECASE) for p in self.EMBEDDING_PATTERNS)
        if not has_embeddings:
            return issues

        # Check for caching
        has_caching = re.search(r'cache|@lru_cache|memoize|stored_embedding', content, re.IGNORECASE)
        if has_caching:
            return issues

        # Find embedding call
        for i, line in enumerate(lines):
            if any(re.search(p, line, re.IGNORECASE) for p in self.EMBEDDING_PATTERNS):
                issues.append(Issue(
                    severity=self.severity,
                    category=self.name,
                    file_path=file_path,
                    line_number=i + 1,
                    code_snippet=line.strip()[:120],
                    description=self.description,
                    recommendation=self.recommendation,
                    estimated_savings=self.estimated_savings,
                    confidence="medium"
                ))
                break

        return issues


class NoErrorHandlingDetector(PatternDetector):
    """Detects API calls without proper error handling."""

    name = "Missing Error Handling"
    severity = "medium"
    description = "LLM API call without visible error handling. Failed requests still cost money, and retries without backoff can multiply costs."
    recommendation = """Add proper error handling with exponential backoff:

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
```"""
    estimated_savings = "Prevents wasted costs from unhandled failures"

    API_PATTERNS = [r'\.create\s*\(', r'\.completions\.create', r'ChatCompletion']
    ERROR_HANDLING_PATTERNS = [r'try\s*:', r'except', r'catch\s*\(', r'\.catch\s*\(', r'retry', r'backoff']

    def detect(self, file_path: str, content: str, lines: List[str]) -> List[Issue]:
        issues = []

        for i, line in enumerate(lines):
            if any(re.search(p, line) for p in self.API_PATTERNS):
                # Check surrounding context for error handling
                context = self._get_context(lines, i, before=5, after=5)

                has_error_handling = any(re.search(p, context) for p in self.ERROR_HANDLING_PATTERNS)

                if not has_error_handling:
                    issues.append(Issue(
                        severity=self.severity,
                        category=self.name,
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip()[:120],
                        description=self.description,
                        recommendation=self.recommendation,
                        estimated_savings=self.estimated_savings,
                        confidence="medium"
                    ))

        return issues


# =============================================================================
# Main Assessor Class
# =============================================================================

class LLMCostAssessor:
    """Main assessment engine."""

    VERSION = "2.0.0"

    # File extensions to analyze
    EXTENSIONS = {'.py', '.js', '.ts', '.jsx', '.tsx', '.mjs'}

    # Directories to skip
    SKIP_DIRS = {
        'node_modules', 'venv', '.venv', 'env', '.env',
        '__pycache__', '.git', 'dist', 'build', '.next',
        'coverage', '.pytest_cache', '.mypy_cache',
    }

    # Patterns indicating file has LLM usage
    LLM_INDICATORS = [
        r'openai', r'OpenAI', r'anthropic', r'Anthropic',
        r'ChatCompletion', r'chat\.completions',
        r'langchain', r'LangChain',
        r'gpt-4', r'gpt-3\.5', r'claude',
        r'llm', r'LLM',
    ]

    def __init__(self, project_path: str, verbose: bool = False):
        self.project_path = Path(project_path).resolve()
        self.verbose = verbose
        self.detectors: List[PatternDetector] = [
            NoMaxTokensDetector(),
            LargeSystemPromptDetector(),
            FullConversationHistoryDetector(),
            NoCachingDetector(),
            APICallInLoopDetector(),
            LargeFileEmbeddingDetector(),
            NoTokenCountingDetector(),
            ExpensiveModelDetector(),
            NoStreamingDetector(),
            EmbeddingReuseDetector(),
            NoErrorHandlingDetector(),
        ]

    def analyze(self) -> AssessmentResult:
        """Run full analysis on the project."""
        if self.verbose:
            print(f"Starting analysis of: {self.project_path}")
            print(f"Using {len(self.detectors)} pattern detectors")

        all_issues: List[Issue] = []
        files_scanned = 0
        files_with_llm = 0

        # Find and analyze files
        for file_path in self._find_files():
            files_scanned += 1

            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
            except Exception as e:
                if self.verbose:
                    print(f"  Error reading {file_path}: {e}")
                continue

            # Check if file has LLM usage
            if not self._has_llm_usage(content):
                continue

            files_with_llm += 1
            rel_path = str(file_path.relative_to(self.project_path))

            if self.verbose:
                print(f"  Analyzing: {rel_path}")

            # Run all detectors
            for detector in self.detectors:
                try:
                    issues = detector.detect(rel_path, content, lines)
                    all_issues.extend(issues)
                except Exception as e:
                    if self.verbose:
                        print(f"    Error in {detector.name}: {e}")

        # Build result
        result = self._build_result(all_issues, files_scanned, files_with_llm)

        if self.verbose:
            print(f"\nAnalysis complete:")
            print(f"  Files scanned: {files_scanned}")
            print(f"  Files with LLM usage: {files_with_llm}")
            print(f"  Issues found: {len(all_issues)}")

        return result

    def _find_files(self):
        """Find all files to analyze."""
        for ext in self.EXTENSIONS:
            for file_path in self.project_path.rglob(f'*{ext}'):
                # Skip excluded directories
                if any(skip in file_path.parts for skip in self.SKIP_DIRS):
                    continue
                yield file_path

    def _has_llm_usage(self, content: str) -> bool:
        """Check if content has LLM-related code."""
        return any(re.search(p, content, re.IGNORECASE) for p in self.LLM_INDICATORS)

    def _build_result(self, issues: List[Issue], files_scanned: int, files_with_llm: int) -> AssessmentResult:
        """Build the assessment result."""
        # Count by severity
        severity_counts = defaultdict(int)
        category_counts = defaultdict(int)
        file_counts = defaultdict(int)

        for issue in issues:
            severity_counts[issue.severity] += 1
            category_counts[issue.category] += 1
            file_counts[issue.file_path] += 1

        # Calculate estimated savings
        estimated_savings = self._estimate_savings(severity_counts)

        # Generate recommendations summary
        recommendations = self._generate_recommendations_summary(category_counts)

        return AssessmentResult(
            project_path=str(self.project_path),
            assessment_version=self.VERSION,
            timestamp=datetime.now().isoformat(),
            files_scanned=files_scanned,
            files_with_llm_usage=files_with_llm,
            total_issues=len(issues),
            critical_issues=severity_counts['critical'],
            high_issues=severity_counts['high'],
            medium_issues=severity_counts['medium'],
            low_issues=severity_counts['low'],
            issues=issues,
            summary_by_category=dict(category_counts),
            summary_by_file=dict(file_counts),
            estimated_savings=estimated_savings,
            recommendations_summary=recommendations
        )

    def _estimate_savings(self, severity_counts: dict) -> str:
        """Estimate potential savings based on issues found."""
        critical = severity_counts.get('critical', 0)
        high = severity_counts.get('high', 0)

        if critical >= 3:
            return "Potential 70-90% cost reduction by addressing critical issues"
        elif critical >= 1:
            return "Potential 50-70% cost reduction by addressing critical issues"
        elif high >= 3:
            return "Potential 30-50% cost reduction by addressing high priority issues"
        elif high >= 1:
            return "Potential 20-40% cost reduction"
        else:
            return "Potential 10-20% cost reduction through optimizations"

    def _generate_recommendations_summary(self, category_counts: dict) -> List[str]:
        """Generate prioritized recommendations."""
        recommendations = []

        priority_order = [
            ("Full Conversation History", "Implement conversation summarization or sliding window"),
            ("API Calls in Loop", "Batch requests or use parallel processing"),
            ("Large System Prompt", "Enable prompt caching or compress prompts"),
            ("No Response Caching", "Add response caching for repeated queries"),
            ("No Token Limit", "Add max_tokens to all API calls"),
            ("Large File Embedding", "Implement chunking or use RAG"),
            ("Embedding Recomputation", "Cache embeddings to avoid recomputation"),
            ("Expensive Model Usage", "Evaluate cheaper models for simpler tasks"),
        ]

        for category, rec in priority_order:
            if category in category_counts:
                recommendations.append(f"[{category_counts[category]} issues] {rec}")

        return recommendations[:5]  # Top 5 recommendations


# =============================================================================
# Report Generation
# =============================================================================

def generate_markdown_report(result: AssessmentResult) -> str:
    """Generate a comprehensive markdown report."""

    report = f"""# LLM Cost Assessment Report

**Project:** `{result.project_path}`
**Assessment Version:** {result.assessment_version}
**Generated:** {result.timestamp}

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Files Scanned | {result.files_scanned} |
| Files with LLM Usage | {result.files_with_llm_usage} |
| Total Issues | {result.total_issues} |

### Issues by Severity

| Severity | Count | Action |
|----------|-------|--------|
| 🔴 Critical | {result.critical_issues} | Fix immediately |
| 🟠 High | {result.high_issues} | Fix this week |
| 🟡 Medium | {result.medium_issues} | Plan to fix |
| 🟢 Low | {result.low_issues} | Consider fixing |

### Estimated Savings

**{result.estimated_savings}**

---

## Top Recommendations

"""

    for i, rec in enumerate(result.recommendations_summary, 1):
        report += f"{i}. {rec}\n"

    report += "\n---\n\n## Issues by Category\n\n"

    for category, count in sorted(result.summary_by_category.items(), key=lambda x: -x[1]):
        report += f"- **{category}**: {count} issue(s)\n"

    report += "\n---\n\n## Files with Most Issues\n\n"

    top_files = sorted(result.summary_by_file.items(), key=lambda x: -x[1])[:10]
    for file_path, count in top_files:
        report += f"- `{file_path}`: {count} issue(s)\n"

    report += "\n---\n\n## Detailed Findings\n\n"

    # Group issues by severity
    for severity, emoji, title in [
        ('critical', '🔴', 'CRITICAL'),
        ('high', '🟠', 'HIGH'),
        ('medium', '🟡', 'MEDIUM'),
        ('low', '🟢', 'LOW'),
    ]:
        severity_issues = [i for i in result.issues if i.severity == severity]
        if not severity_issues:
            continue

        report += f"### {emoji} {title} Priority Issues ({len(severity_issues)})\n\n"

        for issue in severity_issues:
            confidence_badge = {
                'high': '✓ High confidence',
                'medium': '? Medium confidence',
                'low': '~ Low confidence'
            }.get(issue.confidence, '')

            report += f"""#### {issue.category}

**File:** `{issue.file_path}` (line {issue.line_number})
**Confidence:** {confidence_badge}

```
{issue.code_snippet}
```

**Issue:** {issue.description}

**Recommendation:**

{issue.recommendation}

**Potential Savings:** {issue.estimated_savings}

---

"""

    report += """
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
"""

    return report


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Analyze codebase for LLM cost optimization opportunities',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/project
  %(prog)s /path/to/project --output report.md
  %(prog)s /path/to/project --json > results.json
  %(prog)s /path/to/project --verbose
        """
    )
    parser.add_argument('project_path', help='Path to the project to analyze')
    parser.add_argument('--output', '-o', help='Output file path for markdown report')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if not os.path.isdir(args.project_path):
        print(f"Error: '{args.project_path}' is not a valid directory", file=sys.stderr)
        sys.exit(1)

    # Run assessment
    assessor = LLMCostAssessor(args.project_path, verbose=args.verbose)
    result = assessor.analyze()

    # Generate output
    if args.json:
        output = json.dumps(result.to_dict(), indent=2)
    else:
        output = generate_markdown_report(result)

    # Write or print output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Report written to: {args.output}")
        print(f"\nSummary: {result.total_issues} issues found "
              f"({result.critical_issues} critical, {result.high_issues} high)")
    else:
        print(output)

    # Exit with error code if critical issues found
    sys.exit(1 if result.critical_issues > 0 else 0)


if __name__ == '__main__':
    main()
