"use client";
import { useEffect, useRef, useState } from "react";
import { useStudio } from "@/store/studio";
import { Button } from "@/components/ui/Button";
import type { ChatMessage } from "@/types/bracket";

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed whitespace-pre-wrap
          ${isUser
            ? "bg-brand-primary text-white rounded-br-sm"
            : "bg-white border border-slate-200 text-slate-800 rounded-bl-sm"
          }`}
      >
        {msg.content}
      </div>
    </div>
  );
}

export function ChatPane() {
  const { messages, chatLoading, addMessage, setChatLoading, sources, draft } = useStudio();
  const [input, setInput] = useState("");
  const [provider, setProvider] = useState<string>("…");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/api/chat").then((r) => r.json()).then((d) => setProvider(d.provider ?? "none"));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, chatLoading]);

  async function sendMessage() {
    const text = input.trim();
    if (!text || chatLoading) return;
    setInput("");

    const userMsg: ChatMessage = { role: "user", content: text, timestamp: Date.now() };
    addMessage(userMsg);
    setChatLoading(true);

    try {
      // Build context about the current draft
      const draftContext = draft.orchestration.strategic_kpi_id
        ? `\n\nCurrent use case context: "${draft.title}" (${draft.id}), strategic KPI: ${draft.orchestration.strategic_kpi_id}`
        : "";

      const allMessages = [
        ...messages,
        { role: "user" as const, content: text + draftContext },
      ];

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: allMessages,
          sources: sources.filter((s) => s.include_in_chat),
        }),
      });

      const data = await res.json();
      if (data.error) throw new Error(data.error);

      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: data.reply,
        timestamp: Date.now(),
      };
      addMessage(assistantMsg);
    } catch (e) {
      const errMsg: ChatMessage = {
        role: "assistant",
        content: `⚠️ ${e instanceof Error ? e.message : "Chat error"}`,
        timestamp: Date.now(),
      };
      addMessage(errMsg);
    } finally {
      setChatLoading(false);
    }
  }

  const providerLabel: Record<string, string> = {
    gemini: "Gemini ✓",
    azure: "Azure OpenAI ✓",
    openai: "OpenAI ✓",
    none: "No LLM — add API key to .env",
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-3 py-2 border-b border-slate-200 shrink-0 flex items-center justify-between">
        <div>
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Discovery Chat</h2>
          <p className="text-xs text-slate-400 mt-0.5">Ask about KPIs, use cases, and action codes</p>
        </div>
        <span
          className={`text-xs px-2 py-0.5 rounded-full font-medium
            ${provider === "none" ? "bg-red-50 text-red-500" : "bg-green-50 text-green-600"}`}
        >
          {providerLabel[provider] ?? provider}
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-3 py-3">
        {messages.length === 0 && (
          <div className="text-center text-xs text-slate-400 mt-8 space-y-1">
            <p className="font-medium text-slate-500">Start your discovery</p>
            <p>Try: "Suggest a use case for reducing working capital"</p>
            <p>Or: "What KPIs should I track for supply chain reliability?"</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}
        {chatLoading && (
          <div className="flex justify-start mb-3">
            <div className="bg-white border border-slate-200 rounded-lg rounded-bl-sm px-3 py-2">
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-3 py-2 border-t border-slate-200 shrink-0">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Ask about use cases, KPIs, action codes… (Enter to send)"
            rows={2}
            className="flex-1 text-sm border border-slate-200 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-primary resize-none"
          />
          <Button onClick={sendMessage} loading={chatLoading} disabled={!input.trim()}>
            Send
          </Button>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          {sources.filter((s) => s.include_in_chat).length} source(s) in context · Shift+Enter for newline
        </p>
      </div>
    </div>
  );
}
