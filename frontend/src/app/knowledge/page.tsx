"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 24 } },
};

const articles = [
  { title: "Getting Started with OmniFlow", category: "Onboarding", updated: "2 days ago", icon: "rocket_launch", views: 1245 },
  { title: "How to Connect Your WhatsApp", category: "Integrations", updated: "1 week ago", icon: "link", views: 892 },
  { title: "Creating Custom AI Workflows", category: "Workflows", updated: "3 days ago", icon: "account_tree", views: 634 },
  { title: "Understanding Analytics Dashboard", category: "Analytics", updated: "5 days ago", icon: "insights", views: 521 },
  { title: "Agent Training Best Practices", category: "AI Agents", updated: "1 week ago", icon: "school", views: 478 },
  { title: "Handling Escalations & Handoffs", category: "Operations", updated: "4 days ago", icon: "swap_horiz", views: 356 },
];

export default function KnowledgePage() {
  const [search, setSearch] = useState("");

  const filtered = articles.filter(a =>
    a.title.toLowerCase().includes(search.toLowerCase()) ||
    a.category.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <motion.div className="w-full min-h-full p-12" variants={containerVariants} initial="hidden" animate="show">
      <motion.div variants={itemVariants} className="mb-12 flex justify-between items-end">
        <div>
          <h1 className="text-[48px] font-bold text-text-primary tracking-tight leading-tight">Knowledge Base</h1>
          <p className="text-[16px] text-text-secondary mt-2">Your AI agents learn from these articles to provide accurate responses.</p>
        </div>
        <button className="flex items-center gap-2 px-6 py-3 primary-gradient-bg text-white rounded-[20px] text-[16px] font-bold shadow-[0_8px_24px_rgba(79,124,255,0.3)] hover:shadow-[0_12px_32px_rgba(79,124,255,0.4)] hover:-translate-y-0.5 transition-all">
          <span className="material-symbols-outlined text-[20px]">add</span>
          Add Article
        </button>
      </motion.div>

      {/* Search */}
      <motion.div variants={itemVariants} className="mb-10">
        <div className="relative max-w-2xl">
          <span className="absolute left-6 top-1/2 -translate-y-1/2 material-symbols-outlined text-[24px] text-text-muted">search</span>
          <input
            className="w-full bg-white border border-border-strong rounded-[20px] py-4 pl-16 pr-6 text-[16px] text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-4 focus:ring-primary-start/10 transition-all shadow-sm"
            placeholder="Search articles, categories..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </motion.div>

      {/* Articles grid */}
      <motion.div variants={itemVariants} className="grid grid-cols-3 gap-8">
        {filtered.map((article) => (
          <div key={article.title} className="premium-card p-8 cursor-pointer group">
            <div className="flex items-start gap-5 mb-6">
              <div className="w-14 h-14 rounded-[16px] bg-primary-start/10 text-primary-start flex items-center justify-center">
                <span className="material-symbols-outlined text-[28px]">{article.icon}</span>
              </div>
              <span className="px-3 py-1.5 bg-background border border-border-subtle rounded-full text-[12px] font-bold text-text-secondary uppercase tracking-wider">{article.category}</span>
            </div>
            <h3 className="text-[20px] font-bold text-text-primary mb-3 group-hover:text-primary-start transition-colors">{article.title}</h3>
            <div className="flex items-center gap-4 text-[14px] text-text-muted">
              <span className="flex items-center gap-1"><span className="material-symbols-outlined text-[16px]">schedule</span>{article.updated}</span>
              <span className="flex items-center gap-1"><span className="material-symbols-outlined text-[16px]">visibility</span>{article.views}</span>
            </div>
          </div>
        ))}
      </motion.div>
    </motion.div>
  );
}
