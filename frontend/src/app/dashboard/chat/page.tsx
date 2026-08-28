"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useWebsite, WebsiteGate, WebsiteProvider, WebsiteSelector } from "@/components/WebsiteContext";

const suggestions = [
  "Audit my website",
  "What should I fix today?",
  "Find keywords where I can reach the top 10",
  "Analyze my Pune to Mumbai cab page against the top 10 results",
  "Create a prioritized action plan",
];

function ChatContent() {
  const { website } = useWebsite();
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<number | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function send(message: string) {
    if (!website) {
      setError("Select a website before sending a message.");
      return;
    }
    const trimmed = message.trim();
    if (!trimmed || loading) return;

    setError("");
    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.chat(website.id, trimmed, conversationId);
      setConversationId(res.conversation_id);
      setMessages((prev) => [...prev, res.reply]);
      if (res.tasks_created?.length) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Created ${res.tasks_created.length} prioritized task(s). Check the Task Board.`,
          },
        ]);
      }
    } catch (err) {
      const detail = err instanceof Error ? err.message : "Chat request failed";
      setError(detail);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Sorry, I couldn't process that request: ${detail}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <WebsiteGate>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">AI SEO Chat</h2>
            <p className="text-sm text-slate-400">Evidence-based recommendations from your project data</p>
          </div>
          <WebsiteSelector />
        </div>
        <div className="flex flex-wrap gap-2">
          {suggestions.map((s) => (
            <button
              key={s}
              type="button"
              className="rounded-full border border-slate-700 px-3 py-1 text-xs hover:border-brand-500 hover:text-brand-300 disabled:opacity-50"
              disabled={loading}
              onClick={() => send(s)}
            >
              {s}
            </button>
          ))}
        </div>
        <div className="card min-h-[420px] space-y-3">
          {messages.map((m, idx) => (
            <div key={idx} className={`rounded-lg p-3 text-sm ${m.role === "user" ? "bg-brand-700/30" : "bg-slate-800"}`}>
              <p className="mb-1 text-xs uppercase text-slate-400">{m.role}</p>
              <p className="whitespace-pre-wrap">{m.content}</p>
            </div>
          ))}
          {!messages.length && !loading && (
            <p className="text-sm text-slate-400">Ask the AI SEO Manager anything about your website.</p>
          )}
          {loading && (
            <div className="rounded-lg bg-slate-800 p-3 text-sm text-slate-400">
              <p className="mb-1 text-xs uppercase">assistant</p>
              <p>Thinking...</p>
            </div>
          )}
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            void send(input);
          }}
        >
          <input
            className="input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask your AI SEO manager..."
            disabled={loading}
          />
          <button type="submit" className="btn shrink-0" disabled={loading || !input.trim()}>
            {loading ? "Thinking..." : "Send"}
          </button>
        </form>
      </div>
    </WebsiteGate>
  );
}

export default function ChatPage() {
  return (
    <WebsiteProvider>
      <ChatContent />
    </WebsiteProvider>
  );
}
