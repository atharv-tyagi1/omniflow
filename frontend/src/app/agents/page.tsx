"use client";

import React from "react";
import { motion } from "framer-motion";

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } },
};

const agents = [
  { name: "Support Agent", desc: "Handles incoming support tickets, FAQs, and troubleshooting with context-aware responses.", accuracy: "98.6%", handled: "12,482", icon: "support_agent", gradient: "from-[#4F7CFF] to-[#7A5FFF]", bg: "bg-[#4F7CFF]/10", color: "text-[#4F7CFF]", status: "Active" },
  { name: "Sales Agent", desc: "Qualifies leads, answers product questions, and schedules demos with warm personalization.", accuracy: "97.1%", handled: "4,218", icon: "point_of_sale", gradient: "from-[#7A5FFF] to-[#A855F7]", bg: "bg-[#7A5FFF]/10", color: "text-[#7A5FFF]", status: "Active" },
  { name: "Customer Care", desc: "Proactive outreach for renewals, satisfaction surveys, and loyalty programs.", accuracy: "95.4%", handled: "8,735", icon: "favorite", gradient: "from-[#22C55E] to-[#10B981]", bg: "bg-[#22C55E]/10", color: "text-[#22C55E]", status: "Active" },
  { name: "Routing Engine", desc: "Intelligently routes conversations to the right agent based on intent, sentiment, and history.", accuracy: "99.2%", handled: "24,532", icon: "route", gradient: "from-[#F59E0B] to-[#EF4444]", bg: "bg-[#F59E0B]/10", color: "text-[#F59E0B]", status: "Active" },
];

export default function AgentsPage() {
  return (
    <motion.div className="w-full min-h-full p-12" variants={containerVariants} initial="hidden" animate="show">
      <motion.div variants={itemVariants} className="mb-12 flex justify-between items-end">
        <div>
          <h1 className="text-[48px] font-bold text-text-primary tracking-tight leading-tight">AI Agents</h1>
          <p className="text-[16px] text-text-secondary mt-2">Manage and monitor your AI agent fleet.</p>
        </div>
        <button className="flex items-center gap-2 px-6 py-3 primary-gradient-bg text-white rounded-[20px] text-[16px] font-bold shadow-[0_8px_24px_rgba(79,124,255,0.3)] hover:shadow-[0_12px_32px_rgba(79,124,255,0.4)] hover:-translate-y-0.5 transition-all">
          <span className="material-symbols-outlined text-[20px]">add</span>
          Create Agent
        </button>
      </motion.div>

      <motion.div variants={itemVariants} className="grid grid-cols-2 gap-8">
        {agents.map((agent) => (
          <div key={agent.name} className="premium-card overflow-hidden group cursor-pointer">
            <div className={`h-2 w-full bg-gradient-to-r ${agent.gradient}`} />
            <div className="p-10">
              <div className="flex items-start gap-6 mb-8">
                <div className={`w-16 h-16 rounded-[20px] ${agent.bg} ${agent.color} flex items-center justify-center`}>
                  <span className="material-symbols-outlined text-[32px]">{agent.icon}</span>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-[24px] font-bold text-text-primary">{agent.name}</h3>
                    <span className="px-3 py-1 bg-[#22C55E]/10 text-[#22C55E] text-[12px] font-bold uppercase tracking-wider rounded-full">{agent.status}</span>
                  </div>
                  <p className="text-[14px] text-text-secondary leading-relaxed">{agent.desc}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-6">
                <div className="bg-background rounded-[16px] p-5">
                  <p className="text-[14px] text-text-muted mb-1">Accuracy</p>
                  <p className="text-[28px] font-bold text-text-primary">{agent.accuracy}</p>
                </div>
                <div className="bg-background rounded-[16px] p-5">
                  <p className="text-[14px] text-text-muted mb-1">Conversations</p>
                  <p className="text-[28px] font-bold text-text-primary">{agent.handled}</p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </motion.div>
    </motion.div>
  );
}
