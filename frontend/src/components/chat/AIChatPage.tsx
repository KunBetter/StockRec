import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";

interface Message { role: "user" | "ai"; content: string; }

interface AIChatPageProps { onBack: () => void; }

const suggestions = [
  "高股息+低PE有哪些推荐？",
  "宁德时代现在值得入手吗？",
  "帮我对比一下白酒板块的标的",
  "今天AI策略最看好哪个行业？",
];

export default function AIChatPage({ onBack }: AIChatPageProps) {
  const [messages, setMessages] = useState<Message[]>([
    { role: "ai", content: "你好！我是鲸灵宝 AI 助手，基于 DeepSeek 大模型。我可以帮你分析个股、筛选标的、解读市场。试试下面的问题，或者直接问我～" },
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = async (question: string) => {
    if (!question.trim() || streaming) return;
    const userMsg: Message = { role: "user", content: question };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setStreaming(true);

    const aiMsg: Message = { role: "ai", content: "" };
    setMessages(prev => [...prev, aiMsg]);

    try {
      const res = await fetch("/api/v1/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!res.ok || !res.body) throw new Error("Stream not available");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const chunk = line.slice(6);
            if (chunk === "[DONE]") continue;
            setMessages(prev => {
              const next = [...prev];
              next[next.length - 1] = { ...next[next.length - 1], content: next[next.length - 1].content + chunk };
              return next;
            });
          }
        }
      }
    } catch {
      setMessages(prev => {
        const next = [...prev];
        next[next.length - 1] = { ...next[next.length - 1], content: "抱歉，AI 服务暂时不可用，请稍后再试。" };
        return next;
      });
    } finally {
      setStreaming(false);
    }
  };

  return (
    <div className="absolute inset-0 z-50 flex flex-col" style={{ background: "#000000" }}>
      <div className="sticky top-0 z-10 px-5 py-4 flex items-center justify-between"
        style={{ background: "rgba(0,0,0,0.86)", backdropFilter: "blur(20px)" }}>
        <button onClick={onBack} className="text-[17px] font-medium text-[#0A84FF]">← 返回</button>
        <span className="text-[17px] font-semibold">AI 选股助手</span>
        <span className="text-[10px] text-[#636366]">DeepSeek</span>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((m, i) => (
          <motion.div key={i} className={`flex ${m.role === "user" ? "justify-end" : "gap-2"}`}
            initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
            {m.role === "ai" && <span className="text-[16px] flex-shrink-0">🤖</span>}
            <div className={`max-w-[80%] px-3 py-2.5 text-[11px] leading-relaxed ${m.role === "user"
              ? "bg-[#0A84FF] text-white rounded-xl rounded-br-sm"
              : "bg-[rgba(44,44,46,0.7)] text-[#C7C7CC] rounded-xl rounded-bl-sm"}`}>
              {m.content || (streaming && i === messages.length - 1 ? "..." : "")}
            </div>
          </motion.div>
        ))}
        <div ref={bottomRef} />
      </div>

      {messages.length <= 1 && (
        <div className="px-4 pb-2 flex flex-wrap gap-2">
          {suggestions.map((s) => (
            <button key={s} onClick={() => send(s)}
              className="px-3 py-1.5 rounded-full text-[9px] text-[#0A84FF] bg-[rgba(10,132,255,0.08)] border border-[rgba(10,132,255,0.12)]">
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="px-4 py-3">
        <div className="flex gap-2 items-center bg-[rgba(44,44,46,0.6)] rounded-2xl px-4 py-2">
          <span className="text-[16px]">💬</span>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send(input)}
            placeholder="问任何选股问题..."
            className="flex-1 bg-transparent border-none outline-none text-[13px] text-white placeholder-[#636366]"
          />
          <button onClick={() => send(input)} disabled={streaming}
            className="w-6 h-6 rounded-full bg-[#0A84FF] text-white text-[12px] flex items-center justify-center disabled:opacity-40">
            ↑
          </button>
        </div>
      </div>
    </div>
  );
}
