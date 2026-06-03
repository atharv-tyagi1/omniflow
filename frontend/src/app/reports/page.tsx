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

const reports = [
  { name: "Weekly Performance Summary", type: "Auto-generated", date: "Jun 2, 2026", icon: "summarize", pages: 12 },
  { name: "Customer Sentiment Analysis", type: "AI Insight", date: "Jun 1, 2026", icon: "psychology", pages: 8 },
  { name: "Agent Accuracy Report", type: "Auto-generated", date: "May 30, 2026", icon: "fact_check", pages: 6 },
  { name: "Channel Attribution", type: "Custom", date: "May 28, 2026", icon: "attribution", pages: 15 },
  { name: "Monthly Revenue Impact", type: "Executive", date: "May 25, 2026", icon: "payments", pages: 10 },
];

export default function ReportsPage() {
  return (
    <motion.div className="w-full min-h-full p-12" variants={containerVariants} initial="hidden" animate="show">
      <motion.div variants={itemVariants} className="mb-12 flex justify-between items-end">
        <div>
          <h1 className="text-[48px] font-bold text-text-primary tracking-tight leading-tight">Reports</h1>
          <p className="text-[16px] text-text-secondary mt-2">Auto-generated and custom reports powered by your operational data.</p>
        </div>
        <button className="flex items-center gap-2 px-6 py-3 primary-gradient-bg text-white rounded-[20px] text-[16px] font-bold shadow-[0_8px_24px_rgba(79,124,255,0.3)] hover:shadow-[0_12px_32px_rgba(79,124,255,0.4)] hover:-translate-y-0.5 transition-all">
          <span className="material-symbols-outlined text-[20px]">add</span>
          Generate Report
        </button>
      </motion.div>

      <motion.div variants={itemVariants} className="space-y-4">
        {reports.map((r) => (
          <div key={r.name} className="premium-card p-8 flex items-center gap-8 cursor-pointer group">
            <div className="w-16 h-16 rounded-[20px] bg-primary-start/10 text-primary-start flex items-center justify-center">
              <span className="material-symbols-outlined text-[32px]">{r.icon}</span>
            </div>
            <div className="flex-1">
              <h3 className="text-[20px] font-bold text-text-primary group-hover:text-primary-start transition-colors">{r.name}</h3>
              <p className="text-[14px] text-text-secondary mt-1">{r.pages} pages • {r.date}</p>
            </div>
            <span className="px-4 py-2 bg-background border border-border-subtle rounded-full text-[13px] font-bold text-text-secondary">{r.type}</span>
            <div className="flex items-center gap-3">
              <button className="w-10 h-10 rounded-full hover:bg-black/5 flex items-center justify-center text-text-secondary transition-colors">
                <span className="material-symbols-outlined text-[24px]">download</span>
              </button>
              <button className="w-10 h-10 rounded-full hover:bg-black/5 flex items-center justify-center text-text-secondary transition-colors">
                <span className="material-symbols-outlined text-[24px]">share</span>
              </button>
            </div>
          </div>
        ))}
      </motion.div>
    </motion.div>
  );
}
