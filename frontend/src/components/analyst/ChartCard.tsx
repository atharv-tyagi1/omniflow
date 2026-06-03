'use client';

import React from 'react';
import { Maximize2, Download, Filter } from 'lucide-react';

interface ChartCardProps {
  title: string;
  subtitle?: string;
  chartType?: string;
  children: React.ReactNode;
  className?: string;
  bodyClassName?: string;
}

export default function ChartCard({
  title,
  subtitle,
  chartType = 'chart',
  children,
  className = '',
  bodyClassName = 'h-[280px] w-full',
}: ChartCardProps) {
  return (
    <div className={`glass-panel p-6 rounded-3xl animate-slide-up interactive-card ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex flex-col">
          <h3 className="text-sm font-medium text-white tracking-wide">{title}</h3>
          {subtitle && <span className="text-[11px] text-muted-text mt-0.5 uppercase tracking-wider font-semibold">{subtitle}</span>}
        </div>
        <div className="flex items-center gap-3">
          <span className="px-2.5 py-1 rounded-full bg-accent-blue/10 text-accent-blue text-[10px] font-bold tracking-widest uppercase border border-accent-blue/20">
            {chartType}
          </span>
          <div className="flex items-center gap-1">
            <button className="w-8 h-8 rounded-lg flex items-center justify-center text-muted-text hover:text-white hover:bg-white/5 transition-colors" title="Filter">
              <Filter size={14} />
            </button>
            <button className="w-8 h-8 rounded-lg flex items-center justify-center text-muted-text hover:text-white hover:bg-white/5 transition-colors" title="Download">
              <Download size={14} />
            </button>
            <button className="w-8 h-8 rounded-lg flex items-center justify-center text-muted-text hover:text-white hover:bg-white/5 transition-colors" title="Expand">
              <Maximize2 size={14} />
            </button>
          </div>
        </div>
      </div>
      <div className={bodyClassName}>
        {children}
      </div>
    </div>
  );
}
