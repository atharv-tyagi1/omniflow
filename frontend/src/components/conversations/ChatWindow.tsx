"use client";

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { MessageBubble, MessageProps } from './MessageBubble';

interface ChatWindowProps {
  conversationId: string;
  initialMessages: MessageProps[];
  token: string;
}

export const ChatWindow: React.FC<ChatWindowProps> = React.memo(({ conversationId, initialMessages, token }) => {
  const [messages, setMessages] = useState<MessageProps[]>(initialMessages);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom, but use smooth behavior
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages]);

  const handleSend = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isSending) return;

    const content = input.trim();
    setInput('');
    setIsSending(true);

    // Optimistic UI update: instantly show the customer message
    const tempId = `temp-${Date.now()}`;
    const newMsg: MessageProps = {
      id: tempId,
      content,
      sender_type: 'customer',
      created_at: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, newMsg]);

    try {
      const res = await fetch(`http://localhost:8000/api/v1/conversations/${conversationId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ sender_type: 'customer', content })
      });
      
      if (!res.ok) {
        throw new Error("Failed to send message");
      }
      // If we get a response, the backend should return the real message and maybe an AI reply.
      // For now, we keep the optimistic one. A real app would sync IDs.
    } catch (err) {
      console.error("Optimistic update failed:", err);
      // Rollback optimistic update on failure
      setMessages(prev => prev.filter(m => m.id !== tempId));
    } finally {
      setIsSending(false);
    }
  }, [input, isSending, conversationId, token]);

  return (
    <div className="flex flex-col h-full bg-surface/40 backdrop-blur-3xl rounded-3xl border border-white/5 shadow-2xl overflow-hidden">
      
      {/* Header - Glass floating style */}
      <div className="px-8 py-5 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
        <div>
          <h2 className="text-lg font-semibold tracking-tight text-white">Active Conversation</h2>
          <div className="flex items-center gap-2 mt-1">
            <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse"></span>
            <span className="text-[11px] font-medium tracking-widest uppercase text-secondary-text">Connected</span>
          </div>
        </div>
      </div>
      
      {/* Messages Area */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-8 custom-scrollbar relative"
      >
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-muted-text text-sm tracking-wide">
            End-to-end encrypted session started.
          </div>
        ) : (
          <div className="flex flex-col">
            {messages.map(msg => <MessageBubble key={msg.id} message={msg} />)}
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-6 bg-white/[0.02] border-t border-white/5">
        <form onSubmit={handleSend} className="relative flex items-center group">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            disabled={isSending}
            className="w-full pl-6 pr-14 py-4 bg-white/5 border border-white/10 rounded-2xl text-sm text-primary-text placeholder-muted-text focus:outline-none focus:ring-1 focus:ring-accent-blue/50 focus:border-accent-blue/50 transition-all duration-300 disabled:opacity-50"
          />
          <button 
            type="submit"
            disabled={!input.trim() || isSending}
            className="absolute right-3 p-2 rounded-xl text-accent-blue hover:bg-accent-blue hover:text-white disabled:text-muted-text disabled:hover:bg-transparent transition-all duration-200 interactive-btn"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
              <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
});

ChatWindow.displayName = 'ChatWindow';
