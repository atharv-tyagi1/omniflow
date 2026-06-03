"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";

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

export default function AnalystHome() {
  const [query, setQuery] = useState("");

  return (
    <motion.div 
      className="w-full min-h-full p-12 flex flex-col"
      variants={containerVariants}
      initial="hidden"
      animate="show"
    >
      {/* ── Hero Section ── */}
      <motion.section variants={itemVariants} className="w-full max-w-4xl mx-auto text-center space-y-8 mt-10 mb-16">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-[20px] primary-gradient-bg text-white shadow-[0_12px_32px_rgba(79,124,255,0.3)] mb-4">
          <span className="material-symbols-outlined text-[32px]" style={{ fontVariationSettings: "'FILL' 1" }}>auto_awesome</span>
        </div>
        <div className="space-y-4">
          <h2 className="text-[48px] font-bold text-text-primary tracking-tight leading-tight">
            AI Business Analyst
          </h2>
          <p className="text-[16px] text-text-secondary max-w-2xl mx-auto">
            Your data, answered instantly. Upload datasets and ask questions in natural language.
          </p>
        </div>

        {/* Query Bar */}
        <div className="bg-white border border-border-strong rounded-full p-3 pl-8 flex items-center gap-4 shadow-sm relative group transition-all duration-300 focus-within:shadow-[0_12px_40px_rgba(79,124,255,0.15)] focus-within:border-primary-start/40 mt-10">
          <div className="text-primary-start flex items-center pl-2">
            <span className="material-symbols-outlined text-[28px]">auto_awesome</span>
          </div>
          <input
            className="flex-1 bg-transparent border-none focus:ring-0 text-[18px] outline-none text-text-primary placeholder:text-text-muted py-4"
            placeholder="Ask anything about your data..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className="flex items-center gap-3 pr-2">
            <button className="flex items-center gap-2 px-6 py-3 text-text-secondary hover:text-text-primary bg-background hover:bg-black/5 rounded-full transition-colors text-[14px] font-semibold border border-border-subtle">
              <span className="material-symbols-outlined text-[20px]">attach_file</span>
              Data Source
            </button>
            <button className={`w-14 h-14 rounded-full flex items-center justify-center transition-all ${
              query.trim() 
                ? 'primary-gradient-bg text-white shadow-[0_8px_24px_rgba(79,124,255,0.3)] hover:scale-105' 
                : 'bg-background text-text-muted cursor-not-allowed'
            }`}>
              <span className="material-symbols-outlined text-[24px]">send</span>
            </button>
          </div>
        </div>

        {/* Sample Prompts */}
        <div className="flex flex-wrap justify-center gap-4 pt-6">
          {[
            'Show monthly revenue for Q3 by region',
            'Compare top 5 products by sales',
            'Display CAC trends over 6 months',
          ].map((prompt, i) => (
            <motion.button 
              key={prompt} 
              variants={itemVariants}
              onClick={() => setQuery(prompt)}
              className="px-6 py-3 bg-white border border-border-subtle rounded-full text-[14px] font-semibold text-text-secondary hover:text-primary-start hover:border-primary-start/30 transition-all hover:-translate-y-0.5 shadow-sm"
            >
              {prompt}
            </motion.button>
          ))}
        </div>
      </motion.section>

      {/* ── Content Grid ── */}
      <motion.section variants={itemVariants} className="grid grid-cols-12 gap-10 items-start max-w-[1440px] mx-auto w-full">
        
        {/* Left Column: Data Sources */}
        <div className="col-span-4 space-y-8">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-[24px] font-bold text-text-primary flex items-center gap-3">
              <span className="material-symbols-outlined text-text-secondary text-[28px]">database</span>
              Data Connections
            </h3>
            <button className="text-primary-start text-[14px] font-bold hover:text-primary-end transition-colors bg-primary-start/5 px-4 py-2 rounded-full">Manage</button>
          </div>

          <div className="space-y-4">
            {/* Source 1 (Live) */}
            <div className="premium-card p-6 rounded-[24px] flex items-center gap-5 cursor-pointer group">
              <div className="w-16 h-16 rounded-[16px] bg-[#22C55E]/10 flex items-center justify-center text-[#22C55E]">
                <span className="material-symbols-outlined text-[28px]">storage</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-[16px] font-bold text-text-primary truncate group-hover:text-primary-start transition-colors">PostgreSQL - Production</p>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-success"></span>
                  </span>
                  <p className="text-[14px] text-text-secondary font-medium">Live connection</p>
                </div>
              </div>
            </div>

            {/* Source 2 */}
            <div className="premium-card p-6 rounded-[24px] flex items-center gap-5 cursor-pointer group hover:bg-black/[0.02]">
              <div className="w-16 h-16 rounded-[16px] bg-background border border-border-subtle flex items-center justify-center text-text-secondary">
                <span className="material-symbols-outlined text-[32px]">csv</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-[16px] font-bold text-text-primary truncate group-hover:text-primary-start transition-colors">Sales Q3 2024.csv</p>
                </div>
                <p className="text-[14px] text-text-muted font-medium mt-1">2.4 MB • Synced 2h ago</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Recent Analysis / Examples */}
        <div className="col-span-8 space-y-8">
          <div className="premium-card rounded-[32px] overflow-hidden">
            <div className="h-2 w-full primary-gradient-bg"></div>
            <div className="p-10">
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 rounded-[16px] bg-primary-start/10 flex items-center justify-center text-primary-start">
                  <span className="material-symbols-outlined text-[24px]">lightbulb</span>
                </div>
                <div>
                  <h3 className="text-[24px] font-bold text-text-primary">Suggested Insight</h3>
                  <p className="text-[14px] text-text-secondary mt-1">Based on your recent PostgreSQL connection</p>
                </div>
              </div>
              
              <div className="space-y-6 text-[16px] text-text-primary leading-relaxed bg-background p-8 rounded-[24px] border border-border-subtle">
                <p>I noticed a significant anomaly in your latest transaction data:</p>
                <ul className="space-y-5">
                  <li className="flex items-start gap-4">
                    <span className="material-symbols-outlined text-[#F59E0B] mt-0.5 text-[24px]">warning</span>
                    <span>Refund requests in the <strong>Electronics</strong> category spiked by <span className="bg-[#EF4444]/10 text-[#EF4444] px-2 py-1 rounded font-bold">42%</span> over the weekend, primarily driven by SKUs related to "Wireless Headphones".</span>
                  </li>
                  <li className="flex items-start gap-4">
                    <span className="material-symbols-outlined text-[#22C55E] mt-0.5 text-[24px]">check_circle</span>
                    <span>However, overall daily revenue remained stable due to a <span className="bg-[#22C55E]/10 text-[#22C55E] px-2 py-1 rounded font-bold">15% increase</span> in Software Subscription renewals.</span>
                  </li>
                </ul>
              </div>

              <div className="mt-8 flex items-center gap-4">
                <button className="px-6 py-3 bg-primary-start text-white text-[16px] font-bold rounded-[16px] shadow-sm hover:shadow-[0_8px_24px_rgba(79,124,255,0.3)] hover:-translate-y-0.5 transition-all">
                  Generate Full Report
                </button>
                <button className="px-6 py-3 bg-white border border-border-strong text-text-primary text-[16px] font-bold rounded-[16px] hover:bg-black/5 transition-colors">
                  View Raw Data
                </button>
              </div>
            </div>
          </div>
        </div>

      </motion.section>
    </motion.div>
  );
}
