'use client';

import React, { useState } from 'react';
import { ChevronRight, ChevronDown, MessageSquare, BarChart, Database, Zap, Search, HelpCircle } from 'lucide-react';

interface DocSection {
  icon: React.ElementType;
  title: string;
  desc: string;
  content: string[];
}

const docTopics: DocSection[] = [
  {
    icon: MessageSquare,
    title: 'Asking Good Questions',
    desc: 'Learn how to structure your prompts for the best AI analysis.',
    content: [
      'Be specific about what you want: Instead of "show sales", try "Show monthly sales revenue for the past 12 months".',
      'Include time ranges: "Q3 2024", "last 6 months", or "year over year" help narrow results.',
      'Mention the metrics you care about: revenue, units sold, conversion rate, etc.',
      'Use comparison language: "compare", "versus", "top 5", "bottom 10" to get comparative visualizations.',
      'Ask follow-up questions: You can refine your previous query, e.g., "Now break that down by region".',
    ],
  },
  {
    icon: BarChart,
    title: 'Understanding Charts',
    desc: 'A guide to reading the generated visualizations and metrics.',
    content: [
      'Line Charts: Best for showing trends over time. Look for upward/downward patterns and seasonal cycles.',
      'Bar Charts: Compare values across categories. The taller the bar, the higher the value.',
      'Pie/Donut Charts: Show proportions of a whole. Hover over slices to see exact percentages.',
      'Area Charts: Similar to line charts but emphasize volume. Useful for stacked comparisons.',
      'KPI Cards: Show key metrics at a glance with trend indicators (green = up, red = down).',
    ],
  },
  {
    icon: Database,
    title: 'Connecting Data',
    desc: 'How to securely connect your databases or upload CSVs.',
    content: [
      'CSV Upload: Click the upload button or paperclip icon. Drag and drop your CSV file. Supported formats: .csv, .xlsx up to 50MB.',
      'Database Connection: Go to Data Sources → Add Connection. Enter your host, port, database name, and credentials.',
      'Supported Databases: PostgreSQL, MySQL, Snowflake, BigQuery, MongoDB, and more.',
      'Data is never stored permanently on our servers. We only read your data to generate insights.',
      'All connections use SSL/TLS encryption. Credentials are stored encrypted and never shared.',
    ],
  },
  {
    icon: Zap,
    title: 'Advanced Features',
    desc: 'Using predictive analytics and custom reporting.',
    content: [
      'Predictive Queries: Ask "predict next quarter revenue" or "forecast user growth for 6 months".',
      'Custom Dashboards: Pin your favorite queries to create a personal dashboard view.',
      'Scheduled Reports: Set up recurring queries that auto-run and send results to your email.',
      'Export Options: Download any chart as PNG, SVG or PDF. Export data tables as CSV.',
      'Team Sharing: Share queries and dashboards with your team members for collaboration.',
    ],
  },
];

const faqs = [
  { q: 'Is my data secure?', a: 'Yes. All data is encrypted in transit and at rest. We never store your raw data permanently — it is only processed in memory to generate insights.' },
  { q: 'What file formats are supported?', a: 'Currently we support CSV and XLSX files up to 50MB. Database connections support PostgreSQL, MySQL, Snowflake, BigQuery, and MongoDB.' },
  { q: 'Can I share dashboards with my team?', a: 'Yes! Once your dashboard is generated, you can share it via a link or invite team members directly from the settings panel.' },
  { q: 'How accurate are the AI responses?', a: 'Analyst AI uses advanced language models to interpret your questions and generate SQL. Accuracy depends on the clarity of your question and the quality of your data. We always show the generated SQL so you can verify.' },
  { q: 'Is there a free plan?', a: 'Yes, Analyst AI offers a free tier with up to 50 queries per month and 5MB file uploads. Paid plans start at $29/month for unlimited queries.' },
];

export default function Documentation() {
  const [expandedTopic, setExpandedTopic] = useState<number | null>(null);
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredTopics = docTopics.filter(
    (t) =>
      t.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.desc.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredFaqs = faqs.filter(
    (f) =>
      f.q.toLowerCase().includes(searchTerm.toLowerCase()) ||
      f.a.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="max-w-4xl mx-auto space-y-12 animate-fade-in pb-16">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white mb-2">Documentation & Support</h2>
          <p className="text-secondary-text text-sm">Learn how to make the most out of Analyst AI.</p>
        </div>
        <div className="flex items-center gap-3 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-primary-text min-w-[280px] focus-within:border-accent-blue/50 focus-within:bg-white/10 transition-all duration-200">
          <Search size={16} className="text-muted-text" />
          <input
            type="text"
            placeholder="Search docs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-transparent border-none outline-none text-sm w-full placeholder-muted-text"
          />
        </div>
      </div>

      <div className="glass-floating rounded-3xl p-10 text-left relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-accent-blue/10 blur-[80px] rounded-full pointer-events-none"></div>
        <h3 className="text-xl font-bold text-white mb-4 relative z-10">Getting Started with Analyst AI</h3>
        <p className="text-secondary-text leading-relaxed relative z-10 max-w-2xl">
          Welcome to Analyst AI! Our platform allows you to interact with your business data using natural language.
          Simply type a question like "What were our top-selling products last month?" and our AI will generate the appropriate SQL, run it against your data, and visualize the results instantly.
        </p>
      </div>

      <div>
        <h3 className="text-sm font-bold tracking-widest uppercase text-muted-text mb-6">Guides & Topics</h3>
        <div className="space-y-4">
          {filteredTopics.map((topic, i) => (
            <div key={i} className="glass-panel rounded-2xl overflow-hidden interactive-card transition-all duration-300">
              <button
                className="w-full text-left px-6 py-5 flex items-center justify-between"
                onClick={() => setExpandedTopic(expandedTopic === i ? null : i)}
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-accent-blue/10 flex items-center justify-center text-accent-blue border border-accent-blue/20">
                    <topic.icon size={20} />
                  </div>
                  <div>
                    <h4 className="text-base font-semibold text-white tracking-wide">{topic.title}</h4>
                    <p className="text-sm text-secondary-text mt-0.5">{topic.desc}</p>
                  </div>
                </div>
                <div className={`text-muted-text transition-transform duration-300 ${expandedTopic === i ? 'rotate-180' : ''}`}>
                  <ChevronDown size={20} />
                </div>
              </button>
              
              <div 
                className={`overflow-hidden transition-all duration-300 ${expandedTopic === i ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'}`}
              >
                <div className="px-6 pb-6 pt-2 border-t border-white/5 ml-[72px] mr-6">
                  <ul className="space-y-3">
                    {topic.content.map((line, j) => {
                      const [boldPart, rest] = line.split(': ');
                      return (
                        <li key={j} className="text-sm text-secondary-text leading-relaxed flex items-start gap-3">
                          <span className="w-1.5 h-1.5 rounded-full bg-accent-blue/50 mt-1.5 flex-shrink-0"></span>
                          <span>
                            {rest ? (
                              <>
                                <strong className="text-primary-text font-semibold">{boldPart}:</strong> {rest}
                              </>
                            ) : (
                              line
                            )}
                          </span>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-bold tracking-widest uppercase text-muted-text mb-6 flex items-center gap-2">
          <HelpCircle size={16} />
          Frequently Asked Questions
        </h3>
        <div className="space-y-4">
          {filteredFaqs.map((faq, i) => (
            <div key={i} className="glass-panel rounded-2xl overflow-hidden interactive-card transition-all duration-300">
              <button
                className="w-full text-left px-6 py-5 flex items-center justify-between"
                onClick={() => setExpandedFaq(expandedFaq === i ? null : i)}
              >
                <span className="font-medium text-white tracking-wide pr-8">{faq.q}</span>
                <div className={`text-muted-text transition-transform duration-300 flex-shrink-0 ${expandedFaq === i ? 'rotate-180' : ''}`}>
                  <ChevronDown size={18} />
                </div>
              </button>
              <div 
                className={`overflow-hidden transition-all duration-300 ${expandedFaq === i ? 'max-h-[300px] opacity-100' : 'max-h-0 opacity-0'}`}
              >
                <div className="px-6 pb-6 pt-2 border-t border-white/5">
                  <p className="text-sm text-secondary-text leading-relaxed">{faq.a}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
