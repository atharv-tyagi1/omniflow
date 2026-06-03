"use client";

import React, { useState } from "react";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";

const BarChart = dynamic(() => import("recharts").then(mod => mod.BarChart), { ssr: false });
const Bar = dynamic(() => import("recharts").then(mod => mod.Bar), { ssr: false });
const LineChart = dynamic(() => import("recharts").then(mod => mod.LineChart), { ssr: false });
const Line = dynamic(() => import("recharts").then(mod => mod.Line), { ssr: false });
const XAxis = dynamic(() => import("recharts").then(mod => mod.XAxis), { ssr: false });
const YAxis = dynamic(() => import("recharts").then(mod => mod.YAxis), { ssr: false });
const Tooltip = dynamic(() => import("recharts").then(mod => mod.Tooltip), { ssr: false });
const CartesianGrid = dynamic(() => import("recharts").then(mod => mod.CartesianGrid), { ssr: false });
const ResponsiveContainer = dynamic(() => import("recharts").then(mod => mod.ResponsiveContainer), { ssr: false });

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 24 } },
};

const CHART_HEIGHT = { height: 380 } as const;
const TOOLTIP_CONTENT_STYLE = {
  backgroundColor: 'rgba(255,255,255,0.95)',
  backdropFilter: 'blur(24px)',
  borderRadius: '20px',
  border: '1px solid #E5E7EB',
  boxShadow: '0 20px 40px rgba(0,0,0,0.08)',
  padding: '16px'
} as const;
const CHANNEL_COLORS = ['#4F7CFF', '#22C55E', '#7A5FFF', '#F59E0B', '#EF4444'] as const;

const channelData = [
  { name: "Web Chat", conversations: 8420, resolved: 7890, csat: 4.7 },
  { name: "WhatsApp", conversations: 6230, resolved: 5910, csat: 4.8 },
  { name: "Telegram", conversations: 4180, resolved: 3960, csat: 4.5 },
  { name: "Email", conversations: 3450, resolved: 3200, csat: 4.3 },
  { name: "SMS", conversations: 2250, resolved: 2100, csat: 4.6 },
];

const weeklyData = [
  { week: "W1", ai: 3200, human: 480 },
  { week: "W2", ai: 3600, human: 420 },
  { week: "W3", ai: 3100, human: 510 },
  { week: "W4", ai: 4200, human: 380 },
  { week: "W5", ai: 4800, human: 350 },
  { week: "W6", ai: 5100, human: 310 },
];

export default function AnalyticsPage() {
  const [tab, setTab] = useState<"channels" | "agents">("channels");

  return (
    <motion.div className="w-full min-h-full p-12" variants={containerVariants} initial="hidden" animate="show">
      <motion.div variants={itemVariants} className="mb-12 flex justify-between items-end">
        <div>
          <h1 className="text-[48px] font-bold text-text-primary tracking-tight leading-tight">Analytics</h1>
          <p className="text-[16px] text-text-secondary mt-2">Deep dive into your operational metrics across all channels and agents.</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1 p-1.5 bg-white border border-border-subtle rounded-[16px]">
            <button onClick={() => setTab("channels")} className={`px-6 py-2.5 text-[14px] font-semibold rounded-[12px] transition-all ${tab === "channels" ? "bg-primary-start text-white shadow-sm" : "text-text-secondary hover:text-text-primary"}`}>Channels</button>
            <button onClick={() => setTab("agents")} className={`px-6 py-2.5 text-[14px] font-semibold rounded-[12px] transition-all ${tab === "agents" ? "bg-primary-start text-white shadow-sm" : "text-text-secondary hover:text-text-primary"}`}>AI vs Human</button>
          </div>
          <button className="flex items-center gap-2 px-6 py-3 bg-white border border-border-strong rounded-[20px] text-[16px] font-semibold text-text-primary shadow-sm hover:shadow-md transition-shadow">
            <span className="material-symbols-outlined text-[20px]">download</span>
            Export
          </button>
        </div>
      </motion.div>

      {/* KPI Summary Row */}
      <motion.div variants={itemVariants} className="grid grid-cols-4 gap-8 mb-10">
        {[
          { label: "Total Volume", value: "24,530", change: "+18.6%", up: true, icon: "show_chart" },
          { label: "AI Resolution", value: "92.3%", change: "+3.1%", up: true, icon: "smart_toy" },
          { label: "Avg. CSAT", value: "4.6/5", change: "+0.2", up: true, icon: "star" },
          { label: "Avg. First Response", value: "1.2s", change: "-0.4s", up: true, icon: "speed" },
        ].map((kpi) => (
          <div key={kpi.label} className="premium-card p-8">
            <div className="flex items-center gap-3 mb-4">
              <span className="material-symbols-outlined text-[20px] text-text-muted">{kpi.icon}</span>
              <span className="text-[14px] font-medium text-text-secondary">{kpi.label}</span>
            </div>
            <div className="flex items-end justify-between">
              <span className="text-[36px] font-bold text-text-primary tracking-tight">{kpi.value}</span>
              <span className="text-[14px] font-bold text-[#22C55E] flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px]">trending_up</span>{kpi.change}
              </span>
            </div>
          </div>
        ))}
      </motion.div>

      {/* Charts */}
      <motion.div variants={itemVariants} className="grid grid-cols-12 gap-8 mb-10">
        {/* Main chart */}
        <div className="col-span-8 premium-card p-10">
          <h2 className="text-[24px] font-bold text-text-primary mb-2">
            {tab === "channels" ? "Conversations by Channel" : "AI vs Human Resolution"}
          </h2>
          <p className="text-[16px] text-text-secondary mb-8">
            {tab === "channels" ? "Volume distribution across all active channels" : "Weekly AI automation vs human agent handling"}
          </p>
          <div style={CHART_HEIGHT}>
            <ResponsiveContainer width="100%" height="100%">
              {tab === "channels" ? (
                <BarChart data={channelData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                  <CartesianGrid vertical={false} strokeDasharray="4 4" stroke="#E5E7EB" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 14, fontWeight: 500 }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 14, fontWeight: 500 }} />
                  <Tooltip contentStyle={TOOLTIP_CONTENT_STYLE} />
                  <Bar dataKey="conversations" name="Total" fill="#4F7CFF" radius={[8, 8, 0, 0]} />
                  <Bar dataKey="resolved" name="Resolved" fill="#22C55E" radius={[8, 8, 0, 0]} />
                </BarChart>
              ) : (
                <LineChart data={weeklyData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                  <CartesianGrid vertical={false} strokeDasharray="4 4" stroke="#E5E7EB" />
                  <XAxis dataKey="week" axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 14, fontWeight: 500 }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 14, fontWeight: 500 }} />
                  <Tooltip contentStyle={TOOLTIP_CONTENT_STYLE} />
                  <Line type="monotone" dataKey="ai" name="AI Resolved" stroke="#4F7CFF" strokeWidth={4} dot={false} activeDot={{ r: 8, strokeWidth: 0, fill: '#4F7CFF' }} />
                  <Line type="monotone" dataKey="human" name="Human Handled" stroke="#F59E0B" strokeWidth={4} dot={false} activeDot={{ r: 8, strokeWidth: 0, fill: '#F59E0B' }} />
                </LineChart>
              )}
            </ResponsiveContainer>
          </div>
        </div>

        {/* Channel breakdown */}
        <div className="col-span-4 premium-card p-10 flex flex-col">
          <h2 className="text-[24px] font-bold text-text-primary mb-2">Channel Health</h2>
          <p className="text-[16px] text-text-secondary mb-8">CSAT scores per channel</p>
          <div className="flex flex-col gap-6 flex-1 justify-center">
            {channelData.map((ch, i) => {

              return (
                <div key={ch.name} className="group">
                  <div className="flex justify-between items-end mb-2">
                    <span className="text-[16px] font-semibold text-text-primary">{ch.name}</span>
                    <span className="text-[16px] font-bold" style={{ color: CHANNEL_COLORS[i] }}>{ch.csat}/5.0</span>
                  </div>
                  <div className="w-full bg-background rounded-full h-3 overflow-hidden">
                    <motion.div
                      className="h-full rounded-full"
                      style={{ backgroundColor: CHANNEL_COLORS[i] }}
                      initial={{ width: 0 }}
                      animate={{ width: `${(ch.csat / 5) * 100}%` }}
                      transition={{ duration: 1, delay: i * 0.1 }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
