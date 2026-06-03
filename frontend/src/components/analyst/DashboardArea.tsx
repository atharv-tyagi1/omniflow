'use client';

import React, { useState } from 'react';
import { DollarSign, Users, ShoppingCart, BarChart3, Sparkles, Send, Paperclip, ChevronDown, Zap, Shield, TrendingUp, Globe } from 'lucide-react';
import KPICard from './KPICard';
import ChartCard from './ChartCard';
import {
  RevenueLineChart,
  SalesBarChart,
  CategoryPieChart,
  UserGrowthAreaChart,
} from './SampleCharts';

const kpiData = [
  {
    title: 'Total Revenue',
    value: '$842K',
    trend: 12.5,
    trendLabel: 'vs last month',
    icon: <DollarSign size={20} />,
    iconColor: 'blue' as const,
    sparklineData: [
      { value: 30 }, { value: 45 }, { value: 42 }, { value: 55 },
      { value: 50 }, { value: 62 }, { value: 58 }, { value: 70 },
      { value: 68 }, { value: 75 }, { value: 80 }, { value: 85 },
    ],
  },
  {
    title: 'Active Users',
    value: '5,120',
    trend: 8.3,
    trendLabel: 'vs last month',
    icon: <Users size={20} />,
    iconColor: 'green' as const,
    sparklineData: [
      { value: 20 }, { value: 25 }, { value: 30 }, { value: 28 },
      { value: 35 }, { value: 40 }, { value: 38 }, { value: 45 },
      { value: 50 }, { value: 48 }, { value: 55 }, { value: 60 },
    ],
  },
  {
    title: 'Total Orders',
    value: '12,847',
    trend: -2.1,
    trendLabel: 'vs last week',
    icon: <ShoppingCart size={20} />,
    iconColor: 'purple' as const,
    sparklineData: [
      { value: 50 }, { value: 48 }, { value: 52 }, { value: 45 },
      { value: 47 }, { value: 43 }, { value: 46 }, { value: 40 },
      { value: 42 }, { value: 38 }, { value: 41 }, { value: 39 },
    ],
  },
  {
    title: 'Avg. Order Value',
    value: '$68.50',
    trend: 5.7,
    trendLabel: 'vs last quarter',
    icon: <BarChart3 size={20} />,
    iconColor: 'orange' as const,
    sparklineData: [
      { value: 40 }, { value: 42 }, { value: 45 }, { value: 44 },
      { value: 48 }, { value: 50 }, { value: 49 }, { value: 53 },
      { value: 55 }, { value: 54 }, { value: 58 }, { value: 62 },
    ],
  },
];

interface DashboardAreaProps {
  onUploadClick: () => void;
}

const samplePrompts = [
  'Show monthly revenue for Q3 by region',
  'Compare top 5 products by sales volume',
  'Display customer acquisition cost trends',
  'Revenue breakdown by product category',
];

const benefits = [
  {
    icon: <Zap size={24} />,
    title: 'Instant Answers',
    desc: 'Get results in seconds, not hours. No waiting for analysts to build reports.',
    colorClass: 'text-accent-blue',
    bgClass: 'bg-accent-blue/10 border-accent-blue/20',
  },
  {
    icon: <Shield size={24} />,
    title: 'Secure & Private',
    desc: 'Your data stays yours. Enterprise-grade security with end-to-end encryption.',
    colorClass: 'text-success',
    bgClass: 'bg-success/10 border-success/20',
  },
  {
    icon: <TrendingUp size={24} />,
    title: 'Actionable Insights',
    desc: 'Go beyond raw numbers. AI highlights trends, anomalies, and opportunities.',
    colorClass: 'text-accent-purple',
    bgClass: 'bg-accent-purple/10 border-accent-purple/20',
  },
  {
    icon: <Globe size={24} />,
    title: 'Any Data Source',
    desc: 'CSV, Excel, PostgreSQL, MySQL, Snowflake — connect anything in seconds.',
    colorClass: 'text-warning',
    bgClass: 'bg-orange-500/10 border-orange-500/20',
  },
];

export default function DashboardArea({ onUploadClick }: DashboardAreaProps) {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;

    setIsLoading(true);
    setAiResponse(null);
    setAiError(null);

    try {
      const res = await fetch('http://localhost:8000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query.trim() }),
      });

      const data = await res.json();

      if (data.error) {
        setAiError(data.error);
      } else if (data.response) {
        setAiResponse(data.response);
      } else {
        setAiError('No response received from AI.');
      }
    } catch {
      setAiError('Cannot connect to backend. Make sure the Python server is running on port 8000.');
    } finally {
      setIsLoading(false);
      setQuery('');
    }
  };

  return (
    <div className="max-w-5xl mx-auto pb-32 space-y-32">
      
      {/* ===== SECTION 1: Hero ===== */}
      <section className="text-center pt-16">
        <h1 className="text-5xl font-bold tracking-tighter text-white mb-4">
          AI Business Analyst
        </h1>
        <p className="text-xl text-secondary-text tracking-wide mb-16">
          Your data, answered instantly.
        </p>

        <div className="max-w-3xl mx-auto relative z-20">
          <form onSubmit={handleSubmit} className="relative">
            <div className="flex items-center gap-3 p-2 bg-surface/50 backdrop-blur-2xl border border-white/10 rounded-full shadow-[0_20px_40px_-15px_rgba(0,0,0,0.5)] focus-within:border-accent-blue/50 focus-within:shadow-[0_0_30px_rgba(56,189,248,0.15)] transition-all duration-300">
              <div className="pl-6 text-accent-purple">
                <Sparkles size={24} />
              </div>
              <input
                type="text"
                className="flex-1 bg-transparent border-none outline-none text-lg text-white placeholder-muted-text py-4"
                placeholder="Ask AI Business Analyst anything about your data..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <button
                type="button"
                className="p-4 rounded-full text-secondary-text hover:text-white hover:bg-white/5 transition-colors"
                onClick={onUploadClick}
                title="Upload CSV"
              >
                <Paperclip size={20} />
              </button>
              <button 
                type="submit" 
                className="w-14 h-14 mr-1 rounded-full bg-white text-background flex items-center justify-center hover:scale-95 transition-transform duration-200"
                title="Send query"
              >
                <Send size={20} className="ml-1" />
              </button>
            </div>
          </form>

          <div className="flex flex-wrap justify-center gap-3 mt-8">
            {samplePrompts.map((prompt) => (
              <button
                key={prompt}
                className="px-5 py-2 rounded-full bg-white/5 border border-white/10 text-xs font-medium tracking-wide text-secondary-text hover:bg-white/10 hover:text-white hover:border-white/20 transition-all duration-200 interactive-btn"
                onClick={() => setQuery(prompt)}
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* AI Response Area */}
          {isLoading && (
            <div className="mt-12 glass-panel rounded-3xl p-8 text-left animate-pulse">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-6 h-6 rounded-full bg-accent-blue/20"></div>
                <div className="h-4 w-32 bg-white/10 rounded"></div>
              </div>
              <div className="space-y-3">
                <div className="h-4 w-full bg-white/5 rounded"></div>
                <div className="h-4 w-5/6 bg-white/5 rounded"></div>
                <div className="h-4 w-4/6 bg-white/5 rounded"></div>
              </div>
            </div>
          )}

          {aiError && !isLoading && (
            <div className="mt-12 glass-panel border-error/30 rounded-3xl p-8 text-left">
              <div className="flex items-center gap-3 mb-4 text-error">
                <Sparkles size={20} />
                <span className="font-semibold tracking-wide">Error</span>
              </div>
              <div className="text-secondary-text leading-relaxed">{aiError}</div>
            </div>
          )}

          {aiResponse && !isLoading && (
            <div className="mt-12 glass-floating rounded-3xl p-10 text-left">
              <div className="flex items-center gap-3 mb-8 text-accent-blue">
                <Sparkles size={20} />
                <span className="font-semibold tracking-wide uppercase text-xs">AI Business Analyst Response</span>
              </div>
              <div className="text-primary-text leading-relaxed text-[15px]" dangerouslySetInnerHTML={{
                __html: aiResponse
                  .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
                  .replace(/\n/g, '<br/>')
                  .replace(/^- /gm, '• ')
              }} />
            </div>
          )}
        </div>

        {!aiResponse && !aiError && !isLoading && (
          <div className="mt-32 flex flex-col items-center opacity-30 text-muted-text">
            <span className="text-xs uppercase tracking-widest mb-4">Discover More</span>
            <ChevronDown size={20} className="animate-bounce" />
          </div>
        )}
      </section>


      {/* ===== SECTION 2: What is Query AI ===== */}
      <section className="text-center">
        <h2 className="text-3xl font-bold tracking-tight text-white mb-6">What is AI Business Analyst?</h2>
        <p className="text-secondary-text leading-relaxed max-w-2xl mx-auto mb-16">
          A conversational business intelligence platform that transforms the way you interact with data.
          Instead of writing complex SQL or waiting for reports, simply ask a question in plain English.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
          {[
            { num: '01', title: 'Natural Language', desc: 'Type questions like "What were our top-selling products last quarter?" — no coding required.' },
            { num: '02', title: 'Smart Visualizations', desc: 'AI automatically picks the best chart type for your data — bar, line, pie, or table.' },
            { num: '03', title: 'Real-Time Analysis', desc: 'Connect live databases and get up-to-the-minute insights without manual refresh.' }
          ].map(feature => (
            <div key={feature.num} className="glass-panel p-8 rounded-3xl interactive-card">
              <div className="text-xs font-mono text-accent-blue mb-4">{feature.num}</div>
              <h3 className="text-lg font-semibold text-white mb-3">{feature.title}</h3>
              <p className="text-sm text-secondary-text leading-relaxed">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>


      {/* ===== SECTION 3: How It Helps ===== */}
      <section className="text-center">
        <h2 className="text-3xl font-bold tracking-tight text-white mb-6">How It Helps You</h2>
        <p className="text-secondary-text leading-relaxed max-w-2xl mx-auto mb-16">
          Turn complex data into clear, actionable business decisions.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
          {benefits.map((b, i) => (
            <div key={i} className="glass-panel p-8 rounded-3xl interactive-card flex gap-6">
              <div className={`w-14 h-14 rounded-2xl flex items-center justify-center border flex-shrink-0 ${b.bgClass} ${b.colorClass}`}>
                {b.icon}
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">{b.title}</h3>
                <p className="text-sm text-secondary-text leading-relaxed">{b.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ===== SECTION 4: Example Output ===== */}
      <section className="text-center">
        <h2 className="text-3xl font-bold tracking-tight text-white mb-6">Example Output</h2>
        <p className="text-secondary-text leading-relaxed max-w-2xl mx-auto mb-16">
          Here's what AI Business Analyst can generate for you dynamically.
        </p>

        <div className="space-y-6 text-left">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {kpiData.map((kpi, i) => (
              <KPICard key={kpi.title} {...kpi} delay={i * 80} />
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <ChartCard title="Monthly Revenue" subtitle="Revenue vs Target for 2024" chartType="Line">
                <RevenueLineChart />
              </ChartCard>
            </div>
            <div>
              <ChartCard title="Product Categories" subtitle="Distribution by category" chartType="Donut">
                <CategoryPieChart />
              </ChartCard>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartCard title="Sales by Region" subtitle="Regional performance breakdown" chartType="Bar">
              <SalesBarChart />
            </ChartCard>
            <ChartCard title="User Growth" subtitle="Total vs Active users over time" chartType="Area">
              <UserGrowthAreaChart />
            </ChartCard>
          </div>
        </div>
      </section>

    </div>
  );
}
