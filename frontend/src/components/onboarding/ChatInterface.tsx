"use client";

import { useEffect, useRef, useState } from "react";
import { Send } from "lucide-react";
import { v4 as uuidv4 } from "uuid";
import { api, ApiError } from "@/lib/api";
import type { ChatResponse, SourceClause } from "@/types";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: SourceClause[];
}

const SUGGESTED = [
  "What are our non-negotiables on indemnification?",
  "What's our standard position on governing law?",
  "What should I flag in a termination clause?",
  "What's the typical liability cap structure we use?",
  "What IP ownership terms do we always insist on?",
];

const SESSION_KEY = "lexonboard_chat_session";

function getOrCreateSession(): string {
  const stored = sessionStorage.getItem(SESSION_KEY);
  if (stored) return stored;
  const id = uuidv4();
  sessionStorage.setItem(SESSION_KEY, id);
  return id;
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [expandedSource, setExpandedSource] = useState<SourceClause | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const sessionId = useRef<string>("");

  useEffect(() => {
    sessionId.current = getOrCreateSession();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(text: string) {
    if (!text.trim() || loading) return;
    const question = text.trim();
    setInput("");

    const userMsg: Message = { role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    const history = messages.slice(-8).map((m) => ({ role: m.role, content: m.content }));

    try {
      const result = await api.post<ChatResponse>("/api/chat/query", {
        question,
        conversation_history: history,
        session_id: sessionId.current,
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: result.answer, sources: result.sources },
      ]);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Unable to connect. Make sure your documents have been processed.";
      setMessages((prev) => [...prev, { role: "assistant", content: `⚠ ${msg}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-0">
      {/* Suggested questions panel */}
      <aside className="w-56 shrink-0 pr-4 hidden lg:block">
        <p className="text-xs font-semibold text-[#64748B] uppercase tracking-wider mb-3">Suggested</p>
        <div className="space-y-2">
          {SUGGESTED.map((q, i) => (
            <button
              key={i}
              onClick={() => send(q)}
              className="w-full text-left text-xs text-[#8899BB] px-3 py-2.5 rounded border border-[#1E2D4A] hover:border-[#C9A84C]/40 hover:text-[#F5F3EE] transition-colors leading-snug"
            >
              {q}
            </button>
          ))}
        </div>
      </aside>

      {/* Main chat */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          {messages.length === 0 && (
            <div className="text-center py-16 text-[#64748B]">
              <p className="text-lg font-[family-name:var(--font-playfair)] text-[#F5F3EE] mb-2">
                Ask the Playbook
              </p>
              <p className="text-sm">Your org&apos;s contract knowledge, on demand.</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] space-y-2`}>
                <div
                  className={[
                    "rounded-lg px-4 py-3 text-sm leading-relaxed",
                    msg.role === "user"
                      ? "bg-[#C9A84C] text-[#0F1729] font-medium"
                      : "bg-[#1A2540] text-[#F5F3EE]",
                  ].join(" ")}
                >
                  {msg.content}
                </div>

                {msg.sources && msg.sources.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {msg.sources.map((src) => (
                      <button
                        key={src.id}
                        onClick={() => setExpandedSource(src)}
                        className="flex items-center gap-1.5 text-xs bg-[#0D1829] border border-[#1E2D4A] rounded px-2.5 py-1.5 text-[#8899BB] hover:border-[#C9A84C]/40 hover:text-[#F5F3EE] transition-colors text-left"
                      >
                        <span className="text-[#C9A84C] font-medium shrink-0">
                          {src.clause_type.replace(/_/g, " ")}
                        </span>
                        <span className="truncate max-w-[140px]">
                          {src.excerpt.slice(0, 60)}…
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-[#1A2540] rounded-lg px-5 py-4">
                <div className="flex gap-1.5 items-center">
                  {[0, 1, 2].map((i) => (
                    <span
                      key={i}
                      className="w-1.5 h-1.5 bg-[#64748B] rounded-full animate-bounce"
                      style={{ animationDelay: `${i * 150}ms` }}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="pt-4 border-t border-[#1E2D4A]">
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), send(input))}
              placeholder="Ask about contract terms, positions, red flags…"
              className="flex-1 bg-[#0D1829] border border-[#1E2D4A] rounded-md px-4 py-3 text-sm text-[#F5F3EE] placeholder-[#64748B] focus:outline-none focus:border-[#C9A84C] transition-colors"
            />
            <button
              onClick={() => send(input)}
              disabled={!input.trim() || loading}
              className="bg-[#C9A84C] text-[#0F1729] px-4 rounded-md hover:bg-[#B8963E] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={16} />
            </button>
          </div>
          <p className="text-[10px] text-[#64748B] mt-2 text-center">
            Powered by your organization&apos;s contract history
          </p>
        </div>
      </div>

      {/* Source slide-out panel */}
      {expandedSource && (
        <div className="fixed inset-0 z-50 flex justify-end" onClick={() => setExpandedSource(null)}>
          <div
            className="w-96 bg-[#0A1020] border-l border-[#1E2D4A] h-full p-6 overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold text-[#C9A84C] uppercase tracking-wider">
                {expandedSource.clause_type.replace(/_/g, " ")}
              </span>
              <button onClick={() => setExpandedSource(null)} className="text-[#64748B] hover:text-[#F5F3EE]">
                ✕
              </button>
            </div>
            {expandedSource.section_path.length > 0 && (
              <p className="text-xs text-[#64748B] mb-3">
                {expandedSource.section_path.join(" › ")}
              </p>
            )}
            <p className="text-sm text-[#8899BB] leading-relaxed">{expandedSource.excerpt}</p>
          </div>
        </div>
      )}
    </div>
  );
}
