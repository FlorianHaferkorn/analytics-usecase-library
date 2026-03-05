"""
Discovery Chat: build context from included sources and call LLM.
Supports: Google Gemini, Azure OpenAI, OpenAI. No API key → placeholder message.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional

# Max chars per source and total context to avoid blowing the context window
_MAX_CHARS_PER_SOURCE = 4000
_MAX_TOTAL_CONTEXT = 12000


def get_context_from_sources(sources: List[Dict[str, Any]]) -> str:
    """Build a single context string from all sources with include_in_chat=True."""
    parts: List[str] = []
    total = 0
    for src in sources:
        if not src.get("include_in_chat", True):
            continue
        name = src.get("name") or src.get("id") or "Source"
        # Prefer fetched URL content when available
        fetched = src.get("fetched_content")
        content = src.get("content_or_url") or ""
        if isinstance(fetched, str) and fetched.strip():
            chunk = fetched.strip()
        elif isinstance(content, str) and content.strip():
            if content.startswith("http"):
                chunk = f"[URL: {content}]\n(Inhalt nicht geladen. Bei der Quelle auf „Inhalt laden“ klicken.)"
            else:
                chunk = content.strip()
        else:
            continue
        if chunk:
            if len(chunk) > _MAX_CHARS_PER_SOURCE:
                chunk = chunk[:_MAX_CHARS_PER_SOURCE] + "\n… (gekürzt)"
            part = f"--- {name} ---\n{chunk}"
            if total + len(part) > _MAX_TOTAL_CONTEXT:
                part = part[: _MAX_TOTAL_CONTEXT - total] + "\n… (context limit)"
                parts.append(part)
                break
            parts.append(part)
            total += len(part)
    if not parts:
        return ""
    return "\n\n".join(parts)


def _get_system_prompt(catalog_snapshot: Dict[str, Any]) -> str:
    kpi_ids = catalog_snapshot.get("kpi_ids") or []
    action_ids = catalog_snapshot.get("action_code_ids") or []
    kpi_sample = ", ".join(kpi_ids[:25]) + ("…" if len(kpi_ids) > 25 else "")
    action_sample = ", ".join(action_ids[:15]) + ("…" if len(action_ids) > 15 else "")
    return f"""You help derive strategy and KPIs from the provided sources for a Business Steering / Golden Thread framework.

When the user asks for strategic KPIs, influencing KPIs, or action codes:
- Prefer IDs that exist in the catalog. KPI IDs (examples): {kpi_sample}. Action code IDs (examples): {action_sample}.
- If you suggest an ID not in the catalog, say so and use a clear naming pattern (e.g. domain.metric.name for KPIs, C-M2.1-style for action codes).
- One strategic KPI per use case; multiple influencing KPIs; link action codes that drive decisions.

Answer in clear prose. When you suggest a strategic KPI, influencing KPIs, or action codes, always add at the end a JSON block that the app can use to fill the value-driver tree. Use this exact format (replace with your suggested IDs):

```json
{{"strategic_kpi_id": "domain.topic.metric", "influencing_kpi_ids": ["id1", "id2"], "action_code_ids": ["C-S1.1", "F-C1.2"]}}
```

This allows the user to apply your suggestion in one click."""


def call_llm(
    user_message: str,
    context_from_sources: str,
    catalog_snapshot: Dict[str, Any],
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Call LLM (Google Gemini, Azure OpenAI, or OpenAI). Returns assistant reply or error/placeholder if no API key.
    Priority: Gemini (GOOGLE_API_KEY / GEMINI_API_KEY) → Azure → OpenAI.
    """
    google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    api_key = os.environ.get("OPENAI_API_KEY")
    azure_key = os.environ.get("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

    if not google_key and not api_key and not (azure_key and azure_endpoint):
        return (
            "Discovery Chat is not configured. Set one of: **GOOGLE_API_KEY** or **GEMINI_API_KEY** (Google Gemini), "
            "**OPENAI_API_KEY** (OpenAI), or **AZURE_OPENAI_API_KEY** + **AZURE_OPENAI_ENDPOINT** + **AZURE_OPENAI_DEPLOYMENT**."
        )

    system = _get_system_prompt(catalog_snapshot)
    if context_from_sources.strip():
        user_with_context = f"Sources (use these for context):\n\n{context_from_sources}\n\n--- User message ---\n{user_message}"
    else:
        user_with_context = user_message

    messages: List[Dict[str, str]] = [{"role": "system", "content": system}]
    if chat_history:
        for m in chat_history[-10:]:
            messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_with_context})

    try:
        if google_key:
            return _call_gemini(system, user_with_context, chat_history)
        if azure_key and azure_endpoint:
            return _call_azure(messages, azure_endpoint, azure_key, azure_deployment)
        return _call_openai(messages, api_key)
    except Exception as e:
        return f"Error calling LLM: {e}"


def _call_gemini(
    system_prompt: str,
    user_with_context: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """Call Google Gemini (google-generativeai). Uses GOOGLE_API_KEY or GEMINI_API_KEY."""
    try:
        import google.generativeai as genai
    except ImportError:
        pip_cmd = f'"{sys.executable}" -m pip install google-generativeai'
        return (
            "The **google-generativeai** package is not installed in this app's Python environment. "
            "Run the following in a terminal (then restart the app):\n\n"
            f"```\n{pip_cmd}\n```\n\n"
            "Or from repo root: `pip install -r tooling/golden_thread_discovery_studio/requirements.txt`"
        )
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    # Optionally prepend recent history so the model has context
    if chat_history:
        history_blob = "\n\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in chat_history[-6:]
        )
        user_with_context = f"Previous conversation:\n{history_blob}\n\n---\n\n{user_with_context}"
    # system_instruction supported in recent google-generativeai
    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt,
        )
    except TypeError:
        model = genai.GenerativeModel(model_name=model_name)
        user_with_context = f"{system_prompt}\n\n---\n\n{user_with_context}"
    response = model.generate_content(user_with_context)
    if response and response.text:
        return response.text
    return "(No response)"


def _call_azure(messages: List[Dict[str, str]], endpoint: str, key: str, deployment: str) -> str:
    try:
        from openai import AzureOpenAI
    except ImportError:
        return (
            "The **openai** package is not installed. From the repo root run:\n\n"
            "```\npip install openai\n```\n\nOr install all studio deps: "
            "`pip install -r tooling/golden_thread_discovery_studio/requirements.txt`"
        )
    client = AzureOpenAI(azure_endpoint=endpoint.rstrip("/"), api_key=key, api_version="2024-02-15-preview")
    r = client.chat.completions.create(model=deployment, messages=messages, max_tokens=1500)
    if r.choices:
        return r.choices[0].message.content or ""
    return "(No response)"


def _call_openai(messages: List[Dict[str, str]], api_key: str) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        return (
            "The **openai** package is not installed. From the repo root run:\n\n"
            "```\npip install openai\n```\n\nOr install all studio deps: "
            "`pip install -r tooling/golden_thread_discovery_studio/requirements.txt`"
        )
    client = OpenAI(api_key=api_key)
    r = client.chat.completions.create(model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), messages=messages, max_tokens=1500)
    if r.choices:
        return r.choices[0].message.content or ""
    return "(No response)"
