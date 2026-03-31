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
            ? "bg-brand-mint text-brand-petrol rounded-br-sm"
            : "bg-theme border border-theme text-theme rounded-bl-sm"
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
  const [provider, setProvider] = useState<string>("...");
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
        content: `Error: ${e instanceof Error ? e.message : "Chat error"}`,
        timestamp: Date.now(),
      };
      addMessage(errMsg);
    } finally {
      setChatLoading(false);
    }
  }

  const providerLabel: Record<string, string> = {
    gemini: "Gemini",
    azure: "Azure OpenAI",
    openai: "OpenAI",
    none: "No LLM configured",
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-3 py-2 border-b border-theme shrink-0 flex items-center justify-between">
        <div>
          <h2 className="text-xs font-semibold text-theme-tertiary uppercase tracking-wider">Discovery Chat</h2>
          <p className="text-[10px] text-theme-tertiary mt-0.5">Ask about KPIs, use cases, and action codes</p>
        </div>
        <span
          className={`text-[10px] px-2 py-0.5 rounded font-medium
            ${provider === "none"
              ? "bg-nagarro-pink-100 text-nagarro-pink-400 dark:bg-nagarro-pink-900/30 dark:text-nagarro-pink-300"
              : "bg-nagarro-green-100 text-nagarro-green-700 dark:bg-nagarro-green-900/30 dark:text-nagarro-green-300"}`}
        >
          {providerLabel[provider] ?? provider}
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-3 py-3">
        {messages.length === 0 && (
          <div className="text-center text-xs text-theme-tertiary mt-8 space-y-1">
            <p className="font-medium text-theme-secondary">Start your discovery</p>
            <p>Try: &ldquo;Suggest a use case for reducing working capital&rdquo;</p>
            <p>Or: &ldquo;What KPIs should I track for supply chain reliability?&rdquo;</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}
        {chatLoading && (
          <div className="flex justify-start mb-3">
            <div className="bg-theme border border-theme rounded-lg rounded-bl-sm px-3 py-2">
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    className="w-1.5 h-1.5 rounded-full bg-brand-mint animate-bounce"
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
      <div className="px-3 py-2 border-t border-theme shrink-0">
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
            placeholder="Ask about use cases, KPIs, action codes..."
            rows={2}
            className="flex-1 text-sm bg-theme-secondary border border-theme rounded-md px-3 py-2 text-theme focus:outline-none focus:ring-1 focus:ring-brand-mint resize-none placeholder:text-theme-tertiary"
          />
          <Button onClick={sendMessage} loading={chatLoading} disabled={!input.trim()}>
            Send
          </Button>
        </div>
        <p className="text-[10px] text-theme-tertiary mt-1">
          {sources.filter((s) => s.include_in_chat).length} source(s) in context
        </p>
      </div>
    </div>
  );
}
