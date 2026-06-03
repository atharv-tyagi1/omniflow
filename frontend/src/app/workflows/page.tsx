"use client";

import React from "react";
import { motion } from "framer-motion";

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 24 } },
};

const workflows = [
  { name: "New Lead Qualification", status: "Active", triggers: 342, icon: "filter_alt", color: "#4F7CFF", steps: 5 },
  { name: "Support Ticket Triage", status: "Active", triggers: 1287, icon: "sort", color: "#22C55E", steps: 4 },
  { name: "Feedback Collection", status: "Paused", triggers: 89, icon: "rate_review", color: "#F59E0B", steps: 3 },
  { name: "Escalation Handler", status: "Active", triggers: 156, icon: "priority_high", color: "#EF4444", steps: 6 },
  { name: "Onboarding Sequence", status: "Draft", triggers: 0, icon: "waving_hand", color: "#7A5FFF", steps: 8 },
];

export default function WorkflowsPage() {
  return (
    <motion.div className="w-full min-h-full p-12" variants={containerVariants} initial="hidden" animate="show">
      <motion.div variants={itemVariants} className="mb-12 flex justify-between items-end">
        <div>
          <h1 className="text-[48px] font-bold text-text-primary tracking-tight leading-tight">Workflows</h1>
          <p className="text-[16px] text-text-secondary mt-2">Automate complex multi-step processes with visual flow builders.</p>
        </div>
        <button className="flex items-center gap-2 px-6 py-3 primary-gradient-bg text-white rounded-[20px] text-[16px] font-bold shadow-[0_8px_24px_rgba(79,124,255,0.3)] hover:shadow-[0_12px_32px_rgba(79,124,255,0.4)] hover:-translate-y-0.5 transition-all">
          <span className="material-symbols-outlined text-[20px]">add</span>
          New Workflow
        </button>
      </motion.div>

      <motion.div variants={itemVariants} className="space-y-4">
        {workflows.map((wf) => (
          <div key={wf.name} className="premium-card p-8 flex items-center gap-8 cursor-pointer group">
            <div className="w-16 h-16 rounded-[20px] flex items-center justify-center" style={{ backgroundColor: `${wf.color}15`, color: wf.color }}>
              <span className="material-symbols-outlined text-[32px]">{wf.icon}</span>
            </div>
            <div className="flex-1">
              <h3 className="text-[20px] font-bold text-text-primary group-hover:text-primary-start transition-colors">{wf.name}</h3>
              <p className="text-[14px] text-text-secondary mt-1">{wf.steps} steps in flow</p>
            </div>
            <div className="text-center px-8">
              <p className="text-[28px] font-bold text-text-primary">{wf.triggers.toLocaleString()}</p>
              <p className="text-[12px] text-text-muted uppercase tracking-wider font-semibold mt-1">Triggers</p>
            </div>
            <span className={`px-4 py-2 rounded-full text-[13px] font-bold uppercase tracking-wider ${
              wf.status === 'Active' ? 'bg-[#22C55E]/10 text-[#22C55E]' :
              wf.status === 'Paused' ? 'bg-[#F59E0B]/10 text-[#F59E0B]' :
              'bg-black/5 text-text-muted'
            }`}>{wf.status}</span>
            <span className="material-symbols-outlined text-text-muted text-[24px] group-hover:text-text-primary transition-colors">chevron_right</span>
          </div>
        ))}
      </motion.div>
    </motion.div>
  );
}
