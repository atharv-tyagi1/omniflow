import React from 'react';
import Link from 'next/link';
import ProtectedRoute from '@/components/ProtectedRoute';

// Mock initial state for the UI preview. Hardcoding timestamps to fix the useMemo / impure function error in Server Components.
const time1 = "2026-01-01T10:00:00.000Z";
const time2 = "2026-01-01T09:00:00.000Z";

const mockConversations = [
  { id: '11111111-1111-1111-1111-111111111111', customer_id: 'User A', status: 'active', channel: 'web', created_at: time1 },
  { id: '22222222-2222-2222-2222-222222222222', customer_id: 'User B', status: 'resolved', channel: 'email', created_at: time2 },
];

export default function ConversationsPage() {
  return (
    <ProtectedRoute>
      <div className="p-8 max-w-5xl mx-auto min-h-screen flex flex-col relative text-primary-text">
        {/* Background System */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[10%] left-[20%] w-[40%] h-[40%] rounded-full bg-accent-blue opacity-[0.03] blur-[100px]"></div>
        <div className="absolute bottom-[10%] right-[20%] w-[40%] h-[40%] rounded-full bg-accent-purple opacity-[0.03] blur-[100px]"></div>
      </div>

      <div className="flex justify-between items-end mb-12 relative z-10">
        <div>
          <h1 className="text-4xl font-semibold tracking-tight text-white mb-2">Live Chats</h1>
          <p className="text-secondary-text text-sm tracking-wide">Manage and respond to customer inquiries in real-time.</p>
        </div>
        <button className="interactive-btn px-5 py-2.5 rounded-xl bg-accent-blue text-white text-sm font-medium tracking-wide hover:bg-accent-blue/90 transition-colors shadow-[0_0_20px_rgba(56,189,248,0.3)]">
          New Chat
        </button>
      </div>

      <div className="glass-panel border border-white/5 rounded-3xl overflow-hidden flex-1 relative z-10">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-white/5 border-b border-white/5 text-[10px] uppercase tracking-widest text-muted-text font-semibold">
              <th className="p-5 pl-8">ID</th>
              <th className="p-5">Customer</th>
              <th className="p-5">Channel</th>
              <th className="p-5">Status</th>
              <th className="p-5 text-right pr-8">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {mockConversations.map(conv => (
              <tr key={conv.id} className="hover:bg-white/[0.02] transition-colors group">
                <td className="p-5 pl-8 text-sm font-medium text-white tracking-wide">
                  {conv.id.split('-')[0]}
                </td>
                <td className="p-5 text-sm text-secondary-text">{conv.customer_id}</td>
                <td className="p-5">
                  <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase bg-accent-blue/10 text-accent-blue border border-accent-blue/20">
                    {conv.channel}
                  </span>
                </td>
                <td className="p-5">
                  <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase border ${
                    conv.status === 'active' 
                      ? 'bg-success/10 text-success border-success/20' 
                      : 'bg-white/5 text-muted-text border-white/10'
                  }`}>
                    {conv.status}
                  </span>
                </td>
                <td className="p-5 text-right pr-8">
                  <Link 
                    href={`/conversations/${conv.id}`}
                    className="inline-block px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-semibold tracking-wide text-white transition-colors"
                  >
                    Open Chat
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
    </ProtectedRoute>
  );
}
