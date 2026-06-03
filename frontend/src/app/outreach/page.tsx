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

const campaigns = [
  { name: "Re-engagement Campaign", channel: "WhatsApp", sent: 2450, opened: 1820, responded: 645, status: "Active", icon: "campaign" },
  { name: "Product Launch Announcement", channel: "Email", sent: 8200, opened: 5740, responded: 1230, status: "Completed", icon: "rocket_launch" },
  { name: "Renewal Reminder", channel: "SMS", sent: 1100, opened: 980, responded: 412, status: "Scheduled", icon: "schedule_send" },
  { name: "Satisfaction Survey", channel: "Web", sent: 3600, opened: 2150, responded: 890, status: "Active", icon: "rate_review" },
];

export default function OutreachPage() {
  return (
    <motion.div className="w-full min-h-full p-12" variants={containerVariants} initial="hidden" animate="show">
      <motion.div variants={itemVariants} className="mb-12 flex justify-between items-end">
        <div>
          <h1 className="text-[48px] font-bold text-text-primary tracking-tight leading-tight">Proactive Outreach</h1>
          <p className="text-[16px] text-text-secondary mt-2">Launch targeted campaigns across channels with AI-powered personalization.</p>
        </div>
        <button className="flex items-center gap-2 px-6 py-3 primary-gradient-bg text-white rounded-[20px] text-[16px] font-bold shadow-[0_8px_24px_rgba(79,124,255,0.3)] hover:shadow-[0_12px_32px_rgba(79,124,255,0.4)] hover:-translate-y-0.5 transition-all">
          <span className="material-symbols-outlined text-[20px]">add</span>
          New Campaign
        </button>
      </motion.div>

      <motion.div variants={itemVariants} className="grid grid-cols-2 gap-8">
        {campaigns.map((c) => (
          <div key={c.name} className="premium-card p-10 cursor-pointer group">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-[16px] bg-primary-start/10 text-primary-start flex items-center justify-center">
                  <span className="material-symbols-outlined text-[28px]">{c.icon}</span>
                </div>
                <div>
                  <h3 className="text-[20px] font-bold text-text-primary group-hover:text-primary-start transition-colors">{c.name}</h3>
                  <p className="text-[14px] text-text-secondary mt-1">via {c.channel}</p>
                </div>
              </div>
              <span className={`px-3.5 py-1.5 rounded-full text-[12px] font-bold uppercase tracking-wider ${
                c.status === 'Active' ? 'bg-[#22C55E]/10 text-[#22C55E]' :
                c.status === 'Completed' ? 'bg-[#4F7CFF]/10 text-[#4F7CFF]' :
                'bg-[#F59E0B]/10 text-[#F59E0B]'
              }`}>{c.status}</span>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-background rounded-[16px] p-5 text-center">
                <p className="text-[24px] font-bold text-text-primary">{c.sent.toLocaleString()}</p>
                <p className="text-[12px] text-text-muted uppercase tracking-wider font-semibold mt-1">Sent</p>
              </div>
              <div className="bg-background rounded-[16px] p-5 text-center">
                <p className="text-[24px] font-bold text-text-primary">{c.opened.toLocaleString()}</p>
                <p className="text-[12px] text-text-muted uppercase tracking-wider font-semibold mt-1">Opened</p>
              </div>
              <div className="bg-background rounded-[16px] p-5 text-center">
                <p className="text-[24px] font-bold text-[#22C55E]">{c.responded.toLocaleString()}</p>
                <p className="text-[12px] text-text-muted uppercase tracking-wider font-semibold mt-1">Replied</p>
              </div>
            </div>
          </div>
        ))}
      </motion.div>
    </motion.div>
  );
}
