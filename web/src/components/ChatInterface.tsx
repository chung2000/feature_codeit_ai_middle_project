"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, FileText, ChevronDown, ChevronRight, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Helper for tailwind classes
function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

interface Source {
  content: string;
  metadata: Record<string, any>;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  loading?: boolean;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: '안녕하세요! 입찰 공고 관련해서 무엇이든 물어보세요.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const stopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
      setMessages(prev => {
        const newMsgs = [...prev];
        if (newMsgs.length > 0 && newMsgs[newMsgs.length - 1].loading) {
          newMsgs[newMsgs.length - 1] = {
            role: 'assistant',
            content: '답변 생성이 중단되었습니다.'
          };
        }
        return newMsgs;
      });
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg, { role: 'assistant', content: '', loading: true }]);
    setInput('');
    setIsLoading(true);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const response = await fetch('http://localhost:8002/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMsg.content }),
        signal: abortController.signal,
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const data = await response.json();

      setMessages(prev => {
        const newMsgs = [...prev];
        // Replace loading message
        newMsgs[newMsgs.length - 1] = {
          role: 'assistant',
          content: data.answer,
          sources: data.sources
        };
        return newMsgs;
      });
      setIsLoading(false);
      abortControllerRef.current = null;

    } catch (error: any) {
      if (error.name === 'AbortError') return;
      console.error('Error:', error);
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs[newMsgs.length - 1] = {
          role: 'assistant',
          content: '죄송합니다. 오류가 발생했습니다. 다시 시도해 주세요.'
        };
        return newMsgs;
      });
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 text-gray-900">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4 flex items-center gap-3 shadow-sm">
        <div className="bg-blue-600 p-2 rounded-lg text-white">
          <Bot size={24} />
        </div>
        <div>
          <h1 className="font-bold text-lg">RAG ChatBot</h1>
          <p className="text-xs text-gray-500">RAG Powered Assistant</p>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((msg, idx) => (
          <div key={idx} className={cn(
            "flex w-full",
            msg.role === 'user' ? "justify-end" : "justify-start"
          )}>
            <div className={cn(
              "max-w-[80%] rounded-2xl px-5 py-3 shadow-sm",
              msg.role === 'user'
                ? "bg-blue-600 text-white rounded-tr-none"
                : "bg-white border border-gray-100 rounded-tl-none"
            )}>
              {/* Message Content */}
              {msg.loading ? (
                <div className="flex items-center gap-2 text-gray-400">
                  <Loader2 className="animate-spin" size={16} />
                  <span>답변 생성 중...</span>
                </div>
              ) : (
                <div className="whitespace-pre-wrap leading-relaxed">
                  {msg.content}
                </div>
              )}

              {/* Sources Accordion */}
              {!msg.loading && msg.sources && msg.sources.length > 0 && (
                <div className="mt-4 pt-3 border-t border-gray-100">
                  <p className="text-xs font-semibold text-gray-500 mb-2 flex items-center gap-1">
                    <FileText size={12} /> 참고 문서 ({msg.sources.length})
                  </p>
                  <div className="space-y-2">
                    {msg.sources.map((src, sIdx) => (
                      <SourceItem key={sIdx} source={src} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t p-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="궁금한 내용을 입력하세요..."
            className="w-full bg-gray-100 text-gray-900 placeholder-gray-500 rounded-full py-4 pl-6 pr-14 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all border border-transparent focus:bg-white"
          />
          <button
            type="button"
            onClick={isLoading ? stopGeneration : undefined}
            disabled={!input.trim() && !isLoading}
            className={cn(
              "absolute right-2 p-2 rounded-full transition-colors",
              isLoading
                ? "bg-red-500 text-white hover:bg-red-600"
                : "bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600"
            )}
          >
            {isLoading ? <div className="w-5 h-5 flex items-center justify-center font-bold text-xs">■</div> : <Send size={20} />}
          </button>
        </form>
        <p className="text-center text-xs text-gray-400 mt-2">
          AI는 실수를 할 수 있습니다. 중요한 정보는 원문을 확인하세요.
        </p>
      </div>
    </div>
  );
}

function SourceItem({ source }: { source: Source }) {
  const [isOpen, setIsOpen] = useState(false);
  const srcName = source.metadata?.source || "Unknown Document";
  const page = source.metadata?.page ? `(p.${source.metadata.page})` : "";

  return (
    <div className="text-sm bg-gray-50 rounded-md overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 hover:bg-gray-100 transition-colors text-left"
      >
        <span className="font-medium text-gray-700 truncate text-xs flex-1">
          {srcName} {page}
        </span>
        {isOpen ? <ChevronDown size={14} className="text-gray-400" /> : <ChevronRight size={14} className="text-gray-400" />}
      </button>
      {isOpen && (
        <div className="px-3 py-2 text-xs text-gray-600 bg-gray-100 border-t border-gray-200 whitespace-pre-wrap">
          {source.content.slice(0, 300)}...
        </div>
      )}
    </div>
  );
}
