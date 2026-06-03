"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

export default function Navigation() {
  const pathname = usePathname();

  // Helper to determine if a route is active
  const isActive = (path: string) => {
    if (path === '/' && pathname !== '/') return false;
    if (path !== '/' && pathname.startsWith(path)) return true;
    return pathname === path;
  };

  return (
    <>
      {/* ── TOP NAVIGATION ── */}
      <header className="absolute top-0 left-[320px] w-[1600px] h-[100px] flex items-center justify-between px-10 z-20 bg-background/80 backdrop-blur-xl border-b border-border-subtle">
        {/* Global Search */}
        <div className="relative w-[480px] group">
          <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none text-text-muted group-focus-within:text-primary-start transition-colors">
            <span className="material-symbols-outlined text-[24px]">search</span>
          </div>
          <input
            type="text"
            className="w-full bg-white border border-border-strong rounded-[20px] py-4 pl-14 pr-16 text-[16px] text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-4 focus:ring-primary-start/10 transition-all shadow-sm group-hover:shadow-md"
            placeholder="Search OmniFlow..."
          />
          <div className="absolute inset-y-0 right-5 flex items-center pointer-events-none">
            <div className="flex items-center gap-1 bg-background px-2.5 py-1.5 rounded-[8px] border border-border-subtle shadow-sm">
              <span className="text-[14px] font-medium text-text-secondary leading-none">⌘</span>
              <span className="text-[14px] font-medium text-text-secondary leading-none">K</span>
            </div>
          </div>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-6">
          <button className="relative w-12 h-12 flex items-center justify-center rounded-[20px] bg-white border border-border-strong text-text-secondary hover:text-text-primary hover:shadow-md transition-all">
            <span className="material-symbols-outlined text-[24px]">notifications</span>
            <span className="absolute top-3 right-3 w-2.5 h-2.5 bg-[#EF4444] rounded-full border-2 border-white"></span>
          </button>
          
          <button className="h-12 px-6 rounded-[20px] primary-gradient-bg text-white text-[16px] font-bold shadow-[0_8px_24px_rgba(79,124,255,0.3)] hover:shadow-[0_12px_32px_rgba(79,124,255,0.4)] hover:-translate-y-0.5 transition-all flex items-center gap-2">
            <span className="material-symbols-outlined text-[20px]">add</span>
            New Action
          </button>
        </div>
      </header>

      {/* ── SIDEBAR ── */}
      <nav className="absolute top-0 left-0 w-[320px] h-[1080px] bg-[#FDFDFE] border-r border-border-subtle flex flex-col z-30 shadow-[4px_0_24px_rgba(0,0,0,0.02)]">
        {/* Brand */}
        <div className="h-[100px] flex items-center px-10 mb-6 border-b border-border-subtle/50">
          <div className="flex items-center gap-4 group cursor-pointer">
            <div className="w-12 h-12 rounded-[16px] primary-gradient-bg flex items-center justify-center shadow-[0_8px_24px_rgba(79,124,255,0.3)] group-hover:scale-105 transition-transform">
              <span className="material-symbols-outlined text-white text-[24px]" style={{ fontVariationSettings: "'FILL' 1" }}>blur_on</span>
            </div>
            <span className="text-[24px] font-bold text-text-primary tracking-tight">OmniFlow</span>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 pb-10 space-y-10">
          
          {/* Section: Overview */}
          <div>
            <ul className="space-y-2">
              <li className="relative">
                {isActive('/') && (
                  <motion.div 
                    layoutId="active-pill" 
                    className="absolute inset-0 bg-primary-start/5 rounded-[20px]" 
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}
                <Link href="/" className={`relative flex items-center gap-4 px-5 py-4 rounded-[20px] transition-colors ${
                  isActive('/') ? 'text-primary-start font-semibold' : 'text-text-secondary hover:text-text-primary hover:bg-black/5'
                }`}>
                  <span className="material-symbols-outlined text-[24px]">{isActive('/') ? 'grid_view' : 'home'}</span>
                  <span className="text-[16px] font-medium">Overview</span>
                </Link>
              </li>
            </ul>
          </div>

          {/* Section 1: AI Operations */}
          <div>
            <h2 className="px-5 text-[14px] font-bold text-text-muted uppercase tracking-wider mb-4">AI Operations</h2>
            <ul className="space-y-2">
              {[
                { path: '/conversations', icon: 'chat', label: 'Conversations' },
                { path: '/agents', icon: 'smart_toy', label: 'AI Agents' },
                { path: '/knowledge', icon: 'library_books', label: 'Knowledge Base' },
                { path: '/workflows', icon: 'account_tree', label: 'Workflows' },
                { path: '/outreach', icon: 'campaign', label: 'Proactive Outreach' }
              ].map(item => {
                const active = isActive(item.path);
                return (
                  <li key={item.label} className="relative">
                    {active && (
                      <motion.div 
                        layoutId="active-pill" 
                        className="absolute inset-0 bg-primary-start/5 rounded-[20px]" 
                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                      />
                    )}
                    <Link href={item.path} className={`relative flex items-center gap-4 px-5 py-4 rounded-[20px] transition-colors ${
                      active ? 'text-primary-start font-semibold' : 'text-text-secondary hover:text-text-primary hover:bg-black/5'
                    }`}>
                      <span className="material-symbols-outlined text-[24px]">{item.icon}</span>
                      <span className="text-[16px] font-medium">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>

          {/* Section 2: Intelligence */}
          <div>
            <h2 className="px-5 text-[14px] font-bold text-text-muted uppercase tracking-wider mb-4">Intelligence</h2>
            <ul className="space-y-2">
              {[
                { path: '/analytics', icon: 'bar_chart', label: 'Analytics' },
                { path: '/analyst', icon: 'insights', label: 'Business Analyst' },
                { path: '/reports', icon: 'description', label: 'Reports' }
              ].map((item, idx) => {
                const active = isActive(item.path);
                return (
                  <li key={item.label} className="relative">
                    {active && (
                      <motion.div 
                        layoutId="active-pill" 
                        className="absolute inset-0 bg-primary-start/5 rounded-[20px]" 
                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                      />
                    )}
                    <Link href={item.path} className={`relative flex items-center gap-4 px-5 py-4 rounded-[20px] transition-colors ${
                      active ? 'text-primary-start font-semibold' : 'text-text-secondary hover:text-text-primary hover:bg-black/5'
                    }`}>
                      <span className="material-symbols-outlined text-[24px]">{item.icon}</span>
                      <span className="text-[16px] font-medium">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>

        {/* Settings & Profile */}
        <div className="p-6 border-t border-border-subtle bg-white">
          <Link href="/settings" className="flex items-center gap-4 px-5 py-4 mb-4 rounded-[20px] text-text-secondary hover:text-text-primary hover:bg-black/5 transition-colors">
            <span className="material-symbols-outlined text-[24px]">settings</span>
            <span className="text-[16px] font-medium">Settings</span>
          </Link>

          <div className="flex items-center gap-4 p-4 rounded-[20px] border border-border-strong bg-[#FDFDFE] shadow-sm hover:shadow-md transition-shadow cursor-pointer">
            <div className="w-12 h-12 rounded-full border border-border-strong flex items-center justify-center bg-background text-[16px] font-bold text-text-primary">
              AM
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[16px] font-bold text-text-primary truncate">Arjun Mehta</p>
              <p className="text-[14px] text-text-muted truncate">Owner</p>
            </div>
            <span className="material-symbols-outlined text-text-muted text-[20px]">unfold_more</span>
          </div>
        </div>
      </nav>
    </>
  );
}
