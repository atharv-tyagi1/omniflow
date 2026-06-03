"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { api } from "@/lib/api";

const LineChart = dynamic(() => import("recharts").then(mod => mod.LineChart), { ssr: false });
const Line = dynamic(() => import("recharts").then(mod => mod.Line), { ssr: false });
const XAxis = dynamic(() => import("recharts").then(mod => mod.XAxis), { ssr: false });
const YAxis = dynamic(() => import("recharts").then(mod => mod.YAxis), { ssr: false });
const Tooltip = dynamic(() => import("recharts").then(mod => mod.Tooltip), { ssr: false });
const CartesianGrid = dynamic(() => import("recharts").then(mod => mod.CartesianGrid), { ssr: false });
const ResponsiveContainer = dynamic(() => import("recharts").then(mod => mod.ResponsiveContainer), { ssr: false });

interface DashboardData {
  kpis: {
    total_conversations: number;
    resolution_rate: number;
    lead_conversion: number;
    open_tickets: number;
  };
  chart_data: { date: string; conversations: number; resolved?: number; unresolved?: number }[];
  recent_activity: { id: string; channel: string; status: string; updated_at: string; user?: string; intent?: string; agent?: string }[];
  sentiment_distribution: { name: string; value: number }[];
  top_topics: { name: string; count: number }[];
}

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { 
    opacity: 1, 
    y: 0,
    transition: { type: "spring", stiffness: 300, damping: 24 }
  }
};

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const json = await api.get<DashboardData>('/api/v1/analytics/dashboard');
      setData(json);
    } catch {
      // Mock data for canvas demonstration
      setData({
        kpis: {
          total_conversations: 24532,
          resolution_rate: 96.2,
          lead_conversion: 18.5,
          open_tickets: 42,
        },
        chart_data: [
          { date: 'May 12', conversations: 120, resolved: 100, unresolved: 20 },
          { date: 'May 13', conversations: 150, resolved: 130, unresolved: 20 },
          { date: 'May 14', conversations: 180, resolved: 150, unresolved: 30 },
          { date: 'May 15', conversations: 140, resolved: 130, unresolved: 10 },
          { date: 'May 16', conversations: 210, resolved: 180, unresolved: 30 },
          { date: 'May 17', conversations: 250, resolved: 210, unresolved: 40 },
          { date: 'May 18', conversations: 190, resolved: 160, unresolved: 30 },
        ],
        recent_activity: [
          { id: '1', channel: 'web', status: 'resolved', updated_at: '2m ago', user: 'Rohit Sharma', intent: 'Order Status Query', agent: 'Customer Care' },
          { id: '2', channel: 'telegram', status: 'resolved', updated_at: '5m ago', user: 'Sneha Iyer', intent: 'Return & Refund', agent: 'Support Agent' },
          { id: '3', channel: 'web', status: 'active', updated_at: 'Just now', user: 'Amit Patel', intent: 'Technical Issue', agent: 'Support Agent' },
          { id: '4', channel: 'whatsapp', status: 'resolved', updated_at: '12m ago', user: 'Priya Singh', intent: 'Product Inquiry', agent: 'Sales Agent' },
        ],
        sentiment_distribution: [],
        top_topics: [
          { name: 'Order Status', count: 324 },
          { name: 'Refund & Returns', count: 187 },
          { name: 'Product Inquiry', count: 146 },
          { name: 'Shipping Delays', count: 121 },
          { name: 'Payment Failure', count: 83 },
        ],
      });
    } finally {
      setTimeout(() => setLoading(false), 400); 
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading || !data) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-6">
          <div className="w-20 h-20 rounded-[24px] bg-white shadow-xl flex items-center justify-center p-5">
             <div className="w-10 h-10 rounded-full border-[4px] border-border-subtle border-t-primary-start animate-spin"></div>
          </div>
          <p className="text-text-secondary text-[16px] font-medium tracking-wide">Syncing Workspace...</p>
        </div>
      </div>
    );
  }

  const maxTopicCount = Math.max(...data.top_topics.map(t => t.count), 1);

  return (
    <motion.div 
      className="w-full min-h-full p-12"
      variants={containerVariants}
      initial="hidden"
      animate="show"
    >
      
      {/* ── Page Header ── */}
      <motion.div variants={itemVariants} className="mb-12 flex justify-between items-end">
        <div>
          <h1 className="text-[48px] font-bold text-text-primary tracking-tight leading-tight">Overview</h1>
          <p className="text-[16px] text-text-secondary mt-2">Here's what's happening across your operations today.</p>
        </div>
        <div className="flex items-center gap-4">
          <button className="flex items-center gap-2 px-6 py-3 bg-white border border-border-strong rounded-[20px] text-[16px] font-semibold text-text-primary shadow-sm hover:shadow-md transition-shadow">
            <span className="material-symbols-outlined text-[20px]">calendar_today</span>
            Last 7 Days
            <span className="material-symbols-outlined text-[20px] ml-2 text-text-muted">expand_more</span>
          </button>
        </div>
      </motion.div>

      {/* ── KPI Row ── */}
      <motion.div variants={itemVariants} className="grid grid-cols-4 gap-8 mb-10">
        
        {/* KPI 1 */}
        <div className="premium-card p-8 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-40 h-40 bg-[#4F7CFF]/5 rounded-bl-[120px] -z-10 transition-transform duration-500 group-hover:scale-125"></div>
          <div className="flex justify-between items-start mb-8">
            <div className="w-14 h-14 rounded-[20px] bg-[#4F7CFF]/10 flex items-center justify-center text-[#4F7CFF]">
              <span className="material-symbols-outlined text-[28px]">chat_bubble</span>
            </div>
            <span className="flex items-center text-[#22C55E] text-[14px] font-semibold bg-[#22C55E]/10 px-3 py-1.5 rounded-full">
              <span className="material-symbols-outlined text-[16px] mr-1">trending_up</span> 18.6%
            </span>
          </div>
          <p className="text-text-secondary text-[16px] font-medium mb-2">Total Conversations</p>
          <h3 className="text-[48px] font-bold text-text-primary tracking-tight leading-none">{data.kpis.total_conversations.toLocaleString()}</h3>
        </div>

        {/* KPI 2 */}
        <div className="premium-card p-8 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-40 h-40 bg-[#22C55E]/5 rounded-bl-[120px] -z-10 transition-transform duration-500 group-hover:scale-125"></div>
          <div className="flex justify-between items-start mb-8">
            <div className="w-14 h-14 rounded-[20px] bg-[#22C55E]/10 flex items-center justify-center text-[#22C55E]">
              <span className="material-symbols-outlined text-[28px]">task_alt</span>
            </div>
            <span className="flex items-center text-[#22C55E] text-[14px] font-semibold bg-[#22C55E]/10 px-3 py-1.5 rounded-full">
              <span className="material-symbols-outlined text-[16px] mr-1">trending_up</span> 3.2%
            </span>
          </div>
          <p className="text-text-secondary text-[16px] font-medium mb-2">Resolution Rate</p>
          <h3 className="text-[48px] font-bold text-text-primary tracking-tight leading-none">{data.kpis.resolution_rate}%</h3>
        </div>

        {/* KPI 3 */}
        <div className="premium-card p-8 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-40 h-40 bg-[#F59E0B]/5 rounded-bl-[120px] -z-10 transition-transform duration-500 group-hover:scale-125"></div>
          <div className="flex justify-between items-start mb-8">
            <div className="w-14 h-14 rounded-[20px] bg-[#F59E0B]/10 flex items-center justify-center text-[#F59E0B]">
              <span className="material-symbols-outlined text-[28px]">grade</span>
            </div>
            <span className="flex items-center text-[#22C55E] text-[14px] font-semibold bg-[#22C55E]/10 px-3 py-1.5 rounded-full">
              <span className="material-symbols-outlined text-[16px] mr-1">trending_up</span> 1.5%
            </span>
          </div>
          <p className="text-text-secondary text-[16px] font-medium mb-2">Satisfaction Score</p>
          <h3 className="text-[48px] font-bold text-text-primary tracking-tight leading-none">4.8<span className="text-[24px] text-text-muted font-medium ml-1">/5.0</span></h3>
        </div>

        {/* KPI 4 */}
        <div className="premium-card p-8 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-40 h-40 bg-[#7A5FFF]/5 rounded-bl-[120px] -z-10 transition-transform duration-500 group-hover:scale-125"></div>
          <div className="flex justify-between items-start mb-8">
            <div className="w-14 h-14 rounded-[20px] bg-[#7A5FFF]/10 flex items-center justify-center text-[#7A5FFF]">
              <span className="material-symbols-outlined text-[28px]">timer</span>
            </div>
            <span className="flex items-center text-[#22C55E] text-[14px] font-semibold bg-[#22C55E]/10 px-3 py-1.5 rounded-full">
              <span className="material-symbols-outlined text-[16px] mr-1">trending_down</span> 12.4%
            </span>
          </div>
          <p className="text-text-secondary text-[16px] font-medium mb-2">Avg. Response Time</p>
          <h3 className="text-[48px] font-bold text-text-primary tracking-tight leading-none">1.2<span className="text-[24px] text-text-muted font-medium ml-1">s</span></h3>
        </div>

      </motion.div>

      {/* ── Main Charts Row ── */}
      <motion.div variants={itemVariants} className="grid grid-cols-12 gap-8 mb-10">
        
        {/* Analytics Chart */}
        <div className="col-span-8 premium-card p-10 flex flex-col min-h-[560px]">
          <div className="flex justify-between items-start mb-10">
            <div>
              <h2 className="text-[24px] font-bold text-text-primary mb-2">Volume & Resolution</h2>
              <p className="text-[16px] text-text-secondary">AI vs Human handoff metrics across all channels</p>
            </div>
            <div className="flex items-center gap-2 p-1.5 bg-background border border-border-subtle rounded-[16px]">
              <button className="px-6 py-2 text-[14px] font-semibold bg-white text-text-primary rounded-[12px] shadow-sm">Daily</button>
              <button className="px-6 py-2 text-[14px] font-medium text-text-secondary hover:text-text-primary transition-colors">Weekly</button>
            </div>
          </div>
          
          <div className="w-full" style={{ height: 380 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.chart_data} margin={{ top: 20, right: 20, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4F7CFF" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#4F7CFF" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} strokeDasharray="4 4" stroke="#E5E7EB" />
                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 14, fontWeight: 500 }} dy={20} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 14, fontWeight: 500 }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                    backdropFilter: 'blur(24px)',
                    borderRadius: '20px', 
                    border: '1px solid #E5E7EB',
                    boxShadow: '0 20px 40px rgba(0,0,0,0.08)',
                    padding: '16px'
                  }} 
                  itemStyle={{ fontSize: '14px', fontWeight: 600 }}
                  labelStyle={{ fontSize: '14px', color: '#64748B', marginBottom: '8px' }}
                />
                <Line type="monotone" dataKey="conversations" name="Total Volume" stroke="#4F7CFF" strokeWidth={4} dot={false} activeDot={{ r: 8, strokeWidth: 0, fill: '#4F7CFF' }} />
                <Line type="monotone" dataKey="resolved" name="AI Resolved" stroke="#22C55E" strokeWidth={4} dot={false} activeDot={{ r: 8, strokeWidth: 0, fill: '#22C55E' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Intents & Topics */}
        <div className="col-span-4 premium-card p-10 flex flex-col">
          <h2 className="text-[24px] font-bold text-text-primary mb-2">Top Topics</h2>
          <p className="text-[16px] text-text-secondary mb-10">What your users are asking about</p>
          
          <div className="flex flex-col gap-8 flex-1 justify-center">
            {data.top_topics.map((topic, i) => {
              const colors = ['#4F7CFF', '#7A5FFF', '#F59E0B', '#22C55E', '#9CA3AF'];
              const pct = (topic.count / maxTopicCount) * 100;
              const color = colors[i % colors.length];
              
              return (
                <div key={topic.name} className="group">
                  <div className="flex justify-between items-end mb-3">
                    <span className="text-[16px] font-semibold text-text-primary group-hover:text-primary-start transition-colors">{topic.name}</span>
                    <span className="text-[16px] font-bold text-text-secondary">{topic.count}</span>
                  </div>
                  <div className="w-full bg-background rounded-full h-3 overflow-hidden">
                    <motion.div 
                      className="h-full rounded-full" 
                      style={{ backgroundColor: color }}
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ duration: 1.2, delay: i * 0.1, ease: "easeOut" }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </motion.div>

      {/* ── Bottom Row ── */}
      <motion.div variants={itemVariants} className="grid grid-cols-12 gap-8 pb-12">
        
        {/* Recent Activity */}
        <div className="col-span-7 premium-card flex flex-col">
          <div className="p-10 pb-6 border-b border-border-subtle flex justify-between items-center">
            <h2 className="text-[24px] font-bold text-text-primary">Recent Activity</h2>
            <Link href="/conversations" className="text-[16px] font-semibold text-primary-start hover:text-primary-end transition-colors bg-primary-start/5 px-4 py-2 rounded-full">View All History</Link>
          </div>
          <div className="p-4">
            {data.recent_activity.map(act => (
              <div key={act.id} className="flex items-center gap-6 p-5 rounded-[20px] hover:bg-black/[0.02] transition-colors cursor-pointer group">
                <div className="w-14 h-14 rounded-full bg-background border border-border-subtle flex items-center justify-center text-[16px] font-bold text-text-secondary group-hover:text-primary-start group-hover:border-primary-start/30 transition-all">
                  {act.user ? act.user.slice(0, 2).toUpperCase() : 'U'}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[16px] font-bold text-text-primary truncate">{act.user || 'Unknown User'}</p>
                  <p className="text-[14px] text-text-secondary truncate mt-1">{act.intent || 'Unknown Intent'}</p>
                </div>
                <div className="w-36">
                  <span className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-[13px] font-bold uppercase tracking-wider ${
                    act.status === 'resolved' ? 'bg-[#22C55E]/10 text-[#22C55E]' :
                    act.status === 'active' ? 'bg-[#4F7CFF]/10 text-[#4F7CFF]' :
                    'bg-[#F59E0B]/10 text-[#F59E0B]'
                  }`}>
                    <span className={`w-2 h-2 rounded-full ${
                      act.status === 'resolved' ? 'bg-[#22C55E]' : 
                      act.status === 'active' ? 'bg-[#4F7CFF]' : 
                      'bg-[#F59E0B]'
                    }`}></span>
                    {act.status}
                  </span>
                </div>
                <div className="w-48 flex items-center gap-2 text-[14px] font-medium text-text-secondary">
                  <span className="material-symbols-outlined text-[20px]">support_agent</span>
                  {act.agent || 'Router'}
                </div>
                <div className="w-24 text-right text-[14px] text-text-muted font-medium">
                  {act.updated_at}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Agents Status */}
        <div className="col-span-5 premium-card flex flex-col">
          <div className="p-10 pb-6 border-b border-border-subtle flex justify-between items-center">
            <h2 className="text-[24px] font-bold text-text-primary">Active Agents</h2>
            <button className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-black/5 text-text-secondary transition-colors"><span className="material-symbols-outlined text-[24px]">add</span></button>
          </div>
          <div className="p-8 flex flex-col gap-6">
            {[
              { label: 'Support Agent', acc: '98.6%', icon: 'support_agent', bg: 'bg-[#4F7CFF]/10', color: 'text-[#4F7CFF]' },
              { label: 'Sales Agent', acc: '97.1%', icon: 'point_of_sale', bg: 'bg-[#7A5FFF]/10', color: 'text-[#7A5FFF]' },
              { label: 'Customer Care', acc: '95.4%', icon: 'favorite', bg: 'bg-[#22C55E]/10', color: 'text-[#22C55E]' },
              { label: 'Routing Engine', acc: '99.2%', icon: 'route', bg: 'bg-black/5', color: 'text-text-primary' },
            ].map(agent => (
              <div key={agent.label} className="flex items-center gap-5 p-5 rounded-[20px] border border-border-subtle bg-background/50 hover:bg-white hover:shadow-[0_8px_24px_rgba(0,0,0,0.04)] hover:-translate-y-0.5 transition-all group cursor-pointer">
                <div className={`w-14 h-14 rounded-[16px] ${agent.bg} ${agent.color} flex items-center justify-center`}>
                  <span className="material-symbols-outlined text-[28px]">{agent.icon}</span>
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-[16px] font-bold text-text-primary">{agent.label}</span>
                    <span className="text-[14px] font-bold text-[#22C55E] flex items-center gap-1">
                      {agent.acc}
                      <span className="material-symbols-outlined text-[16px]">check_circle</span>
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-black/5 overflow-hidden">
                    <div className="h-full bg-[#22C55E] rounded-full transition-all duration-1000" style={{ width: agent.acc }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </motion.div>

    </motion.div>
  );
}
