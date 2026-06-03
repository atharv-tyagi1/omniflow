"use client";

import React, { useState } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import { Settings, User, Building, Moon, Sun, Key, LogOut, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const [activeTab, setActiveTab] = useState('profile');

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'workspace', label: 'Workspace', icon: Building },
    { id: 'appearance', label: 'Appearance', icon: Sun },
    { id: 'api', label: 'API Keys', icon: Key },
  ];

  return (
    <ProtectedRoute>
      <div className="min-h-screen p-6 md:p-8 relative">
        <div className="max-w-[1000px] mx-auto space-y-8 relative z-10">
          
          <header className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/" className="h-10 w-10 flex items-center justify-center rounded-xl bg-hover-bg hover:bg-surface-border transition-colors border border-surface-border text-secondary-text">
                <ArrowLeft className="h-5 w-5" />
              </Link>
              <div>
                <h1 className="text-3xl font-semibold tracking-tight text-primary-text">Settings</h1>
                <p className="text-sm text-secondary-text mt-1">Manage your account and preferences</p>
              </div>
            </div>
            <button 
              onClick={logout}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-error bg-error/10 hover:bg-error/20 transition-colors border border-error/20"
            >
              <LogOut className="h-4 w-4" />
              Sign Out
            </button>
          </header>

          <div className="flex flex-col md:flex-row gap-8">
            
            {/* Sidebar */}
            <aside className="w-full md:w-64 shrink-0 space-y-1">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                    activeTab === tab.id
                      ? 'bg-hover-bg text-primary-text border border-surface-border shadow-sm'
                      : 'text-secondary-text hover:bg-hover-bg/50 hover:text-primary-text border border-transparent'
                  }`}
                >
                  <tab.icon className={`h-4 w-4 ${activeTab === tab.id ? 'text-accent-blue' : ''}`} />
                  {tab.label}
                </button>
              ))}
            </aside>

            {/* Content Area */}
            <main className="flex-1 space-y-6">
              
              {activeTab === 'profile' && (
                <div className="glass-panel rounded-3xl p-8 space-y-6">
                  <div>
                    <h2 className="text-xl font-semibold text-primary-text mb-1">Personal Information</h2>
                    <p className="text-sm text-secondary-text">Update your personal details here.</p>
                  </div>
                  <div className="space-y-4">
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium tracking-wide text-secondary-text uppercase">Full Name</label>
                      <input 
                        type="text" 
                        defaultValue={user?.name || ''} 
                        className="w-full bg-hover-bg border border-surface-border rounded-xl py-2.5 px-4 text-sm text-primary-text focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium tracking-wide text-secondary-text uppercase">Email Address</label>
                      <input 
                        type="email" 
                        defaultValue={user?.email || ''} 
                        disabled
                        className="w-full bg-hover-bg/50 border border-surface-border rounded-xl py-2.5 px-4 text-sm text-muted-text cursor-not-allowed"
                      />
                    </div>
                    <button className="bg-primary-text text-background text-sm font-medium px-6 py-2.5 rounded-xl hover:opacity-90 transition-opacity">
                      Save Changes
                    </button>
                  </div>
                </div>
              )}

              {activeTab === 'workspace' && (
                <div className="glass-panel rounded-3xl p-8 space-y-6">
                  <div>
                    <h2 className="text-xl font-semibold text-primary-text mb-1">Workspace Configuration</h2>
                    <p className="text-sm text-secondary-text">Manage your team's workspace details.</p>
                  </div>
                  <div className="space-y-4">
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium tracking-wide text-secondary-text uppercase">Workspace ID</label>
                      <div className="flex items-center gap-3">
                        <input 
                          type="text" 
                          value={user?.workspace_id || ''} 
                          readOnly
                          className="flex-1 bg-hover-bg/50 border border-surface-border rounded-xl py-2.5 px-4 text-sm font-mono text-muted-text"
                        />
                        <button className="interactive-btn px-4 py-2.5 rounded-xl bg-hover-bg border border-surface-border text-sm font-medium">
                          Copy
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'appearance' && (
                <div className="glass-panel rounded-3xl p-8 space-y-6">
                  <div>
                    <h2 className="text-xl font-semibold text-primary-text mb-1">Theme Preferences</h2>
                    <p className="text-sm text-secondary-text">Customize how OmniFlow looks on your device.</p>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <button 
                      onClick={() => setTheme('light')}
                      className={`flex flex-col items-center justify-center gap-3 p-6 rounded-2xl border-2 transition-all ${
                        theme === 'light' ? 'border-accent-blue bg-accent-blue/5' : 'border-surface-border hover:border-accent-blue/50 bg-hover-bg'
                      }`}
                    >
                      <Sun className={`h-8 w-8 ${theme === 'light' ? 'text-accent-blue' : 'text-secondary-text'}`} />
                      <span className="text-sm font-medium">Light</span>
                    </button>
                    <button 
                      onClick={() => setTheme('dark')}
                      className={`flex flex-col items-center justify-center gap-3 p-6 rounded-2xl border-2 transition-all ${
                        theme === 'dark' ? 'border-accent-purple bg-accent-purple/5' : 'border-surface-border hover:border-accent-purple/50 bg-hover-bg'
                      }`}
                    >
                      <Moon className={`h-8 w-8 ${theme === 'dark' ? 'text-accent-purple' : 'text-secondary-text'}`} />
                      <span className="text-sm font-medium">Dark</span>
                    </button>
                    <button 
                      onClick={() => setTheme('system')}
                      className={`flex flex-col items-center justify-center gap-3 p-6 rounded-2xl border-2 transition-all ${
                        theme === 'system' ? 'border-primary-text bg-hover-bg' : 'border-surface-border hover:border-primary-text/50 bg-hover-bg'
                      }`}
                    >
                      <Settings className={`h-8 w-8 ${theme === 'system' ? 'text-primary-text' : 'text-secondary-text'}`} />
                      <span className="text-sm font-medium">System</span>
                    </button>
                  </div>
                </div>
              )}

              {activeTab === 'api' && (
                <div className="glass-panel rounded-3xl p-8 space-y-6">
                  <div>
                    <h2 className="text-xl font-semibold text-primary-text mb-1">API Integrations</h2>
                    <p className="text-sm text-secondary-text">Manage external services and API keys.</p>
                  </div>
                  <div className="space-y-4">
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium tracking-wide text-secondary-text uppercase">Telegram Bot Token</label>
                      <input 
                        type="password" 
                        placeholder="••••••••••••••••••••••••••••••••"
                        className="w-full bg-hover-bg border border-surface-border rounded-xl py-2.5 px-4 text-sm text-primary-text focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
                      />
                      <p className="text-[10px] text-muted-text mt-1">Leave blank to use environment default.</p>
                    </div>
                    <button className="bg-primary-text text-background text-sm font-medium px-6 py-2.5 rounded-xl hover:opacity-90 transition-opacity">
                      Save Integrations
                    </button>
                  </div>
                </div>
              )}

            </main>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
