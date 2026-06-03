'use client';

import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import dynamic from 'next/dynamic';

const ResponsiveContainer = dynamic(() => import('recharts').then(mod => mod.ResponsiveContainer), { ssr: false });
const AreaChart = dynamic(() => import('recharts').then(mod => mod.AreaChart), { ssr: false });
const Area = dynamic(() => import('recharts').then(mod => mod.Area), { ssr: false });

interface KPICardProps {
  title: string;
  value: string;
  trend: number;
  trendLabel: string;
  icon: React.ReactNode;
  iconColor: 'blue' | 'green' | 'purple' | 'orange';
  sparklineData: { value: number }[];
  delay?: number;
}

const colorMap = {
  blue: 'text-accent-blue bg-accent-blue/10 border-accent-blue/20',
  green: 'text-success bg-success/10 border-success/20',
  purple: 'text-accent-purple bg-accent-purple/10 border-accent-purple/20',
  orange: 'text-warning bg-orange-500/10 border-orange-500/20',
};

export default function KPICard({
  title,
  value,
  trend,
  trendLabel,
  icon,
  iconColor,
  sparklineData,
  delay = 0,
}: KPICardProps) {
  const isUp = trend >= 0;
  const sparkColor = isUp ? '#22c55e' : '#ef4444';

  return (
    <div
      className="glass-panel interactive-card p-6 rounded-3xl flex flex-col justify-between h-full relative overflow-hidden"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-accent-blue to-accent-purple opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
      
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center border ${colorMap[iconColor]}`}>
            {icon}
          </div>
          <div className={`flex items-center gap-1 text-[11px] font-bold tracking-wider uppercase px-2.5 py-1 rounded-full ${isUp ? 'bg-success/10 text-success border border-success/20' : 'bg-error/10 text-error border border-error/20'}`}>
            {isUp ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            {Math.abs(trend)}%
          </div>
        </div>
        <div className="text-3xl font-semibold tracking-tight text-white mb-1">{value}</div>
        <div className="text-xs font-medium text-secondary-text tracking-wide">{title} <span className="text-muted-text">· {trendLabel}</span></div>
      </div>
      
      <div className="h-12 mt-6 -mx-2 -mb-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={sparklineData}>
            <defs>
              <linearGradient id={`spark-${iconColor}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={sparkColor} stopOpacity={0.2} />
                <stop offset="100%" stopColor={sparkColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <Area
              type="monotone"
              dataKey="value"
              stroke={sparkColor}
              strokeWidth={2}
              fill={`url(#spark-${iconColor})`}
              dot={false}
              isAnimationActive={false} // Disable animation for faster render
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
