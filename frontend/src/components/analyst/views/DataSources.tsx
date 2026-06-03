'use client';

import React, { useState } from 'react';
import { Database, Plus, Check, RefreshCw, Trash2, FileSpreadsheet, Server, Cloud } from 'lucide-react';

interface DataSource {
  id: number;
  name: string;
  type: string;
  icon: 'db' | 'file' | 'cloud';
  status: 'connected' | 'syncing' | 'error';
  lastSync: string;
  records: string;
  tables: number;
}

const initialSources: DataSource[] = [
  { id: 1, name: 'Main Production DB', type: 'PostgreSQL', icon: 'db', status: 'connected', lastSync: '10 mins ago', records: '2.4M', tables: 42 },
  { id: 2, name: 'Analytics Warehouse', type: 'Snowflake', icon: 'cloud', status: 'connected', lastSync: '1 hour ago', records: '14.8M', tables: 86 },
  { id: 3, name: 'Legacy Sales Data', type: 'MySQL', icon: 'db', status: 'syncing', lastSync: 'Sync in progress', records: '850K', tables: 21 },
  { id: 4, name: 'BMW Vehicle Inventory', type: 'CSV Upload', icon: 'file', status: 'connected', lastSync: '2 hours ago', records: '4,200', tables: 1 },
  { id: 5, name: 'Marketing Analytics', type: 'BigQuery', icon: 'cloud', status: 'connected', lastSync: '30 mins ago', records: '6.1M', tables: 35 },
  { id: 6, name: 'CRM Database', type: 'MongoDB', icon: 'db', status: 'error', lastSync: 'Connection failed', records: '—', tables: 0 },
];

export default function DataSources() {
  const [sources, setSources] = useState(initialSources);
  const [syncing, setSyncing] = useState<number | null>(null);

  const handleRemove = (id: number) => {
    const source = sources.find((s) => s.id === id);
    if (confirm(`Remove "${source?.name}"? This will disconnect the data source.`)) {
      setSources((prev) => prev.filter((s) => s.id !== id));
    }
  };

  const handleSync = (id: number) => {
    setSyncing(id);
    setSources((prev) =>
      prev.map((s) => (s.id === id ? { ...s, status: 'syncing' as const, lastSync: 'Sync in progress' } : s))
    );
    // Simulate sync completion
    setTimeout(() => {
      setSources((prev) =>
        prev.map((s) => (s.id === id ? { ...s, status: 'connected' as const, lastSync: 'Just now' } : s))
      );
      setSyncing(null);
    }, 2000);
  };

  const handleAddNew = () => {
    alert('Add New Connection\n\nThis feature will be available after API integration.\nYou can currently upload CSV files using the Upload button.');
  };

  const getIcon = (icon: string) => {
    switch (icon) {
      case 'file': return <FileSpreadsheet size={24} />;
      case 'cloud': return <Cloud size={24} />;
      default: return <Database size={24} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'bg-success/10 text-success border border-success/20';
      case 'syncing': return 'bg-warning/10 text-warning border border-warning/20';
      case 'error': return 'bg-error/10 text-error border border-error/20';
      default: return 'bg-white/10 text-white border border-white/20';
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-fade-in pb-12">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white mb-2">Data Sources</h2>
          <p className="text-secondary-text text-sm">Manage your connected databases and integrations.</p>
        </div>
        <button 
          className="interactive-btn px-5 py-2.5 rounded-xl bg-accent-blue text-white text-sm font-semibold tracking-wide flex items-center gap-2 hover:bg-accent-blue/90 transition-colors shadow-[0_0_20px_rgba(56,189,248,0.3)]"
          onClick={handleAddNew}
        >
          <Plus size={16} /> Add Connection
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sources.map((source) => (
          <div key={source.id} className="glass-panel rounded-3xl p-6 interactive-card flex flex-col h-full group">
            <div className="flex items-start justify-between mb-6">
              <div className="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center text-accent-blue border border-white/10 group-hover:bg-accent-blue/10 transition-colors">
                {getIcon(source.icon)}
              </div>
              <div className={`px-2.5 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase flex items-center gap-1.5 ${getStatusColor(source.status)}`}>
                {source.status === 'syncing' && <RefreshCw size={10} className="animate-spin" />}
                {source.status}
              </div>
            </div>
            
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white tracking-tight mb-1">{source.name}</h3>
              <p className="text-sm text-secondary-text">{source.type}</p>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-6 pt-6 border-t border-white/5 mt-auto">
              <div>
                <div className="text-[10px] uppercase tracking-widest text-muted-text mb-1">Records</div>
                <div className="text-sm font-semibold text-white">{source.records}</div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-widest text-muted-text mb-1">Tables</div>
                <div className="text-sm font-semibold text-white">{source.tables > 0 ? source.tables : '—'}</div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-widest text-muted-text mb-1">Last Sync</div>
                <div className="text-sm font-semibold text-white flex items-center gap-1.5 whitespace-nowrap overflow-hidden text-ellipsis">
                  {source.status === 'syncing' ? <RefreshCw size={12} className="animate-spin text-warning" /> : <Check size={12} className="text-success" />}
                  <span className="truncate">{source.lastSync}</span>
                </div>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                className="flex-1 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-semibold tracking-wide text-white transition-colors flex justify-center items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={() => handleSync(source.id)}
                disabled={syncing === source.id}
                title="Re-sync"
              >
                <RefreshCw size={14} className={syncing === source.id ? 'animate-spin' : ''} /> Sync
              </button>
              <button
                className="py-2.5 px-4 rounded-xl bg-error/10 hover:bg-error/20 border border-error/20 text-xs font-semibold tracking-wide text-error transition-colors flex justify-center items-center"
                onClick={() => handleRemove(source.id)}
                title="Remove"
              >
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        ))}

        <div 
          className="glass-panel border-dashed border-2 border-white/10 hover:border-accent-blue/50 rounded-3xl p-6 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300 hover:bg-white/[0.02] min-h-[300px] group"
          onClick={handleAddNew}
        >
          <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center text-muted-text group-hover:text-accent-blue group-hover:bg-accent-blue/10 transition-colors mb-4 border border-white/10">
            <Plus size={32} />
          </div>
          <h3 className="text-lg font-semibold text-white tracking-tight mb-2">Connect New Source</h3>
          <p className="text-sm text-secondary-text max-w-[200px]">PostgreSQL, MySQL, Snowflake, CSV, etc.</p>
        </div>
      </div>
    </div>
  );
}
