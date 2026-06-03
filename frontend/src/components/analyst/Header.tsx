'use client';

import React from 'react';
import { Search, Bell, HelpCircle } from 'lucide-react';

export default function Header() {
  return (
    <header className="flex-shrink-0 h-[84px] px-8 flex items-center justify-between border-b border-white/5 bg-transparent z-10">
      <div className="flex flex-col">
        <h2 className="text-xl font-semibold tracking-tight text-white">Business Analyst</h2>
        <span className="text-xs text-secondary-text mt-1 tracking-wide">Welcome back! Here's your business intelligence overview.</span>
      </div>
      <div className="flex items-center gap-4">
        {/* Command Palette Trigger */}
        <div className="flex items-center gap-3 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-secondary-text cursor-pointer hover:bg-white/10 hover:border-white/20 transition-all duration-200">
          <Search size={16} />
          <span className="text-xs font-medium tracking-wide">Search anything...</span>
          <kbd className="ml-4 px-2 py-0.5 rounded-[4px] bg-white/10 border border-white/10 text-[10px] font-mono text-muted-text">⌘K</kbd>
        </div>
        
        {/* Actions */}
        <div className="flex items-center gap-2">
          <button className="w-9 h-9 rounded-full flex items-center justify-center text-secondary-text hover:bg-white/10 hover:text-white transition-colors">
            <HelpCircle size={18} />
          </button>
          <button className="relative w-9 h-9 rounded-full flex items-center justify-center text-secondary-text hover:bg-white/10 hover:text-white transition-colors">
            <Bell size={18} />
            <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-error border-2 border-background"></span>
          </button>
        </div>

        {/* Profile */}
        <div className="w-9 h-9 rounded-full bg-accent-blue/20 border border-accent-blue/30 flex items-center justify-center text-xs font-semibold text-accent-blue cursor-pointer hover:bg-accent-blue/30 transition-colors ml-2">
          JD
        </div>
      </div>
    </header>
  );
}
