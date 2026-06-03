'use client';

import React, { useState } from 'react';
import { History, Search, FileText, CheckCircle, Clock, AlertCircle, Trash2, RotateCcw, Filter } from 'lucide-react';

const initialHistory = [
  { id: 1, query: 'Show monthly revenue for Q3 by region', date: '2 hours ago', status: 'completed', duration: '1.2s', rows: 24 },
  { id: 2, query: 'Compare top 5 products by sales volume', date: '5 hours ago', status: 'completed', duration: '0.8s', rows: 5 },
  { id: 3, query: 'Display customer acquisition cost trends', date: 'Yesterday', status: 'failed', duration: '4.5s', rows: 0 },
  { id: 4, query: 'Revenue breakdown by product category', date: 'Yesterday', status: 'completed', duration: '2.1s', rows: 8 },
  { id: 5, query: 'What is the churn rate for enterprise customers?', date: '2 days ago', status: 'completed', duration: '1.5s', rows: 1 },
  { id: 6, query: 'Show top 10 customers by lifetime value', date: '2 days ago', status: 'completed', duration: '2.8s', rows: 10 },
  { id: 7, query: 'Monthly active users trend for the past year', date: '3 days ago', status: 'completed', duration: '1.1s', rows: 12 },
  { id: 8, query: 'Compare sales figures Q1 vs Q2 2024', date: '3 days ago', status: 'completed', duration: '0.9s', rows: 6 },
  { id: 9, query: 'Show average order value by region', date: '4 days ago', status: 'failed', duration: '3.2s', rows: 0 },
  { id: 10, query: 'List all products with declining sales', date: '5 days ago', status: 'completed', duration: '1.7s', rows: 14 },
  { id: 11, query: 'What percentage of revenue comes from new customers?', date: '1 week ago', status: 'completed', duration: '2.4s', rows: 1 },
  { id: 12, query: 'Show inventory levels by warehouse', date: '1 week ago', status: 'completed', duration: '1.3s', rows: 7 },
];

export default function QueryHistory() {
  const [history, setHistory] = useState(initialHistory);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'failed'>('all');

  const filtered = history.filter((item) => {
    const matchesSearch = item.query.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || item.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleDelete = (id: number) => {
    setHistory((prev) => prev.filter((item) => item.id !== id));
  };

  const handleRerun = (query: string) => {
    alert(`Re-running query:\n"${query}"\n\n(API integration pending)`);
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-fade-in">
      
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white mb-2">Query History</h2>
          <p className="text-secondary-text text-sm">Review your past interactions with Analyst AI and their results.</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-primary-text min-w-[280px] focus-within:border-accent-blue/50 focus-within:bg-white/10 transition-all duration-200">
            <Search size={16} className="text-muted-text" />
            <input
              type="text"
              placeholder="Search history..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-transparent border-none outline-none text-sm w-full placeholder-muted-text"
            />
          </div>
          <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-primary-text hover:bg-white/10 transition-colors">
            <Filter size={16} className="text-muted-text" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as 'all' | 'completed' | 'failed')}
              className="bg-transparent border-none outline-none text-sm appearance-none cursor-pointer"
            >
              <option value="all" className="bg-surface text-white">All Status</option>
              <option value="completed" className="bg-surface text-white">Completed</option>
              <option value="failed" className="bg-surface text-white">Failed</option>
            </select>
          </div>
        </div>
      </div>

      <div className="glass-panel rounded-3xl overflow-hidden border border-white/5">
        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full text-left text-sm text-secondary-text">
            <thead className="bg-white/5 text-muted-text uppercase text-[10px] tracking-widest font-semibold">
              <tr>
                <th className="px-6 py-4 rounded-tl-3xl">Query</th>
                <th className="px-6 py-4">Time</th>
                <th className="px-6 py-4">Duration</th>
                <th className="px-6 py-4">Rows</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 rounded-tr-3xl text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-16 text-center text-muted-text">
                    No queries match your search criteria.
                  </td>
                </tr>
              ) : (
                filtered.map((item) => (
                  <tr key={item.id} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="px-6 py-5">
                      <div className="flex items-center gap-3 text-white font-medium">
                        <div className="p-2 rounded-lg bg-white/5 text-accent-blue group-hover:bg-accent-blue/10 transition-colors">
                          <FileText size={16} />
                        </div>
                        {item.query}
                      </div>
                    </td>
                    <td className="px-6 py-5 whitespace-nowrap">{item.date}</td>
                    <td className="px-6 py-5 whitespace-nowrap">{item.duration}</td>
                    <td className="px-6 py-5 whitespace-nowrap">{item.rows > 0 ? item.rows : '—'}</td>
                    <td className="px-6 py-5 whitespace-nowrap">
                      {item.status === 'completed' ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-success/10 text-success text-[11px] font-bold tracking-wider uppercase border border-success/20">
                          <CheckCircle size={12} /> Completed
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-error/10 text-error text-[11px] font-bold tracking-wider uppercase border border-error/20">
                          <AlertCircle size={12} /> Failed
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-5 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button 
                          className="p-2 rounded-lg text-secondary-text hover:text-accent-blue hover:bg-accent-blue/10 transition-colors" 
                          title="Re-run Query" 
                          onClick={() => handleRerun(item.query)}
                        >
                          <RotateCcw size={16} />
                        </button>
                        <button 
                          className="p-2 rounded-lg text-secondary-text hover:text-error hover:bg-error/10 transition-colors" 
                          title="Delete" 
                          onClick={() => handleDelete(item.id)}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="px-6 py-4 bg-white/[0.02] border-t border-white/5 text-xs text-muted-text">
          Showing {filtered.length} of {history.length} queries
        </div>
      </div>
    </div>
  );
}
