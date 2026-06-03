'use client';

import React from 'react';
import {
  LayoutDashboard,
  History,
  Database,
  Settings,
  ChevronLeft,
  ChevronRight,
  Zap,
  Upload,
  BookOpen,
} from 'lucide-react';
import Link from 'next/link';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const navItems = [
  { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { id: 'history', icon: History, label: 'Query History' },
  { id: 'sources', icon: Database, label: 'Data Sources' },
  { id: 'upload', icon: Upload, label: 'Upload Data' },
  { id: 'docs', icon: BookOpen, label: 'Documentation' },
  { id: 'settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar({ collapsed, onToggle, activeTab, onTabChange }: SidebarProps) {
  return (
    <aside className={`relative h-full bg-secondary border-r border-white/5 transition-all duration-300 ease-in-out flex flex-col z-20 ${collapsed ? 'w-[80px]' : 'w-[280px]'}`}>
      <button 
        className="absolute -right-3 top-8 w-6 h-6 rounded-full bg-surface border border-white/10 flex items-center justify-center text-secondary-text hover:text-white hover:border-accent-blue hover:bg-accent-blue/10 transition-colors z-30"
        onClick={onToggle}
      >
        {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>

      {/* Logo Area */}
      <div className="flex items-center gap-3 p-6 border-b border-white/5 min-h-[84px]">
        <div className="w-10 h-10 rounded-xl bg-accent-blue/10 border border-accent-blue/20 flex items-center justify-center flex-shrink-0 text-accent-blue shadow-[0_0_15px_rgba(56,189,248,0.2)]">
          <Zap size={20} />
        </div>
        <div className={`flex flex-col overflow-hidden transition-opacity duration-200 ${collapsed ? 'opacity-0 w-0' : 'opacity-100'}`}>
          <h1 className="text-base font-semibold tracking-wide text-white whitespace-nowrap">Analyst AI</h1>
          <span className="text-[10px] text-accent-blue uppercase tracking-widest font-medium">Intelligence</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-6 px-4 flex flex-col gap-1 overflow-y-auto custom-scrollbar">
        <div className={`text-[10px] uppercase tracking-widest text-muted-text mb-2 px-4 transition-opacity duration-200 ${collapsed ? 'opacity-0' : 'opacity-100'}`}>
          Main Menu
        </div>
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group relative ${
                isActive 
                  ? 'bg-accent-blue/10 text-accent-blue' 
                  : 'text-secondary-text hover:bg-white/5 hover:text-white'
              }`}
            >
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-accent-blue rounded-r-md shadow-[0_0_10px_rgba(56,189,248,0.5)]"></div>
              )}
              <item.icon size={20} className="flex-shrink-0" />
              <span className={`text-sm font-medium tracking-wide whitespace-nowrap transition-opacity duration-200 ${collapsed ? 'opacity-0 w-0 hidden' : 'opacity-100'}`}>
                {item.label}
              </span>
            </button>
          );
        })}
      </nav>

      {/* Global Dashboard Link */}
      <div className="p-4 border-t border-white/5">
        <Link href="/" className={`flex items-center gap-3 p-3 rounded-xl hover:bg-white/5 text-muted-text hover:text-white transition-colors ${collapsed ? 'justify-center' : ''}`}>
          <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0 text-xs font-bold text-white">
            OF
          </div>
          <div className={`flex flex-col overflow-hidden transition-opacity duration-200 ${collapsed ? 'opacity-0 w-0 hidden' : 'opacity-100'}`}>
            <span className="text-xs font-medium text-white whitespace-nowrap">OmniFlow Core</span>
            <span className="text-[10px] text-muted-text whitespace-nowrap">Return to Dashboard</span>
          </div>
        </Link>
      </div>
    </aside>
  );
}
