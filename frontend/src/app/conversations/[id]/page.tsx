import React from 'react';
import { ChatWindow } from '@/components/conversations/ChatWindow';

export default async function ConversationDetailPage({ params }: { params: { id: string } }) {
  const { id } = await params;
  
  // In a real app, you would fetch initial messages server-side
  // const res = await fetch(`http://localhost:8000/api/v1/conversations/${id}/messages`);
  // const data = await res.json();
  // const initialMessages = data.data.messages;

  // Mock initial state for the UI preview. Hardcoding timestamps to fix the useMemo / impure function error.
  const time1 = "2026-01-01T10:00:00.000Z";
  const time2 = "2026-01-01T10:01:00.000Z";

  const initialMessages = [
    { id: '1', content: 'Hello, I have an issue with my recent bill.', sender_type: 'customer' as const, created_at: time1 },
    { id: '2', content: 'Hi there! I can help you with that. Can you provide your account number?', sender_type: 'agent' as const, created_at: time2 }
  ];

  return (
    <div className="h-screen bg-background flex flex-col items-center justify-center p-6 relative">
      {/* Background System */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[10%] left-[20%] w-[40%] h-[40%] rounded-full bg-accent-blue opacity-[0.03] blur-[100px]"></div>
        <div className="absolute bottom-[10%] right-[20%] w-[40%] h-[40%] rounded-full bg-accent-purple opacity-[0.03] blur-[100px]"></div>
      </div>

      <div className="w-full max-w-4xl h-[85vh] relative z-10">
        <ChatWindow 
          conversationId={id} 
          initialMessages={initialMessages} 
          token="mock-token-for-now"
        />
      </div>
    </div>
  );
}
