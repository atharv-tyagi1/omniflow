'use client';

import React from 'react';
import { User, Mail, Shield, Palette, LogOut, Moon, Sun, Monitor } from 'lucide-react';
import { useTheme, type Theme } from '@/context/ThemeContext';

const themeOptions: { id: Theme; label: string; icon: React.ElementType; desc: string }[] = [
  { id: 'dark',   label: 'Dark',   icon: Moon,    desc: 'Deep blacks and soft glows' },
  { id: 'light',  label: 'Light',  icon: Sun,     desc: 'Clean whites and crisp contrast' },
  { id: 'system', label: 'System', icon: Monitor, desc: 'Follows your OS preference' },
];

export default function SettingsView() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="max-w-3xl mx-auto space-y-10 animate-fade-in pb-16">

      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight mb-2" style={{ color: 'var(--text-primary)' }}>Settings</h2>
        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Manage your account preferences and app configuration.</p>
      </div>

      {/* ─── Appearance ─── */}
      <section className="glass-panel rounded-3xl p-8 space-y-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-accent-purple/10 text-accent-purple border border-accent-purple/20">
            <Palette size={18} />
          </div>
          <div>
            <h3 className="text-base font-semibold tracking-wide" style={{ color: 'var(--text-primary)' }}>Appearance</h3>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Choose your interface theme</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {themeOptions.map((opt) => {
            const isActive = theme === opt.id;
            return (
              <button
                key={opt.id}
                onClick={() => setTheme(opt.id)}
                className={`relative rounded-2xl p-5 text-left transition-all duration-300 border group cursor-pointer ${
                  isActive
                    ? 'border-accent-blue bg-accent-blue/10 shadow-[0_0_25px_rgba(56,189,248,0.15)]'
                    : 'border-[var(--surface-border)] hover:border-[var(--surface-border-hover)] bg-[var(--hover-bg)] hover:bg-[var(--active-bg)]'
                }`}
              >
                {/* Active indicator dot */}
                {isActive && (
                  <div className="absolute top-3 right-3 w-2.5 h-2.5 rounded-full bg-accent-blue shadow-[0_0_8px_rgba(56,189,248,0.6)]" />
                )}

                <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 transition-colors ${
                  isActive
                    ? 'bg-accent-blue/20 text-accent-blue'
                    : 'bg-[var(--hover-bg)] group-hover:bg-[var(--active-bg)]'
                }`} style={{ color: isActive ? undefined : 'var(--text-muted)' }}>
                  <opt.icon size={22} />
                </div>

                <div className="text-sm font-semibold tracking-wide mb-1" style={{ color: 'var(--text-primary)' }}>
                  {opt.label}
                </div>
                <div className="text-xs leading-relaxed" style={{ color: 'var(--text-muted)' }}>
                  {opt.desc}
                </div>
              </button>
            );
          })}
        </div>
      </section>

      {/* ─── Profile Information ─── */}
      <section className="glass-panel rounded-3xl p-8 space-y-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-accent-blue/10 text-accent-blue border border-accent-blue/20">
            <User size={18} />
          </div>
          <div>
            <h3 className="text-base font-semibold tracking-wide" style={{ color: 'var(--text-primary)' }}>Profile Information</h3>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Your account details</p>
          </div>
        </div>

        <div className="space-y-4">
          {/* Username */}
          <div className="flex items-center justify-between py-3 border-b" style={{ borderColor: 'var(--surface-border)' }}>
            <div className="flex items-center gap-3">
              <User size={16} style={{ color: 'var(--text-muted)' }} />
              <span className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Username</span>
            </div>
            <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>John Doe</span>
          </div>
          {/* Email */}
          <div className="flex items-center justify-between py-3 border-b" style={{ borderColor: 'var(--surface-border)' }}>
            <div className="flex items-center gap-3">
              <Mail size={16} style={{ color: 'var(--text-muted)' }} />
              <span className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Email</span>
            </div>
            <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>john.doe@example.com</span>
          </div>
          {/* Role */}
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3">
              <Shield size={16} style={{ color: 'var(--text-muted)' }} />
              <span className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Role</span>
            </div>
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase bg-accent-blue/10 text-accent-blue border border-accent-blue/20">
              Admin
            </span>
          </div>
        </div>

        <button className="interactive-btn px-5 py-2.5 rounded-xl bg-accent-blue text-white text-sm font-semibold tracking-wide hover:bg-accent-blue/90 transition-colors shadow-[0_0_20px_rgba(56,189,248,0.2)]">
          Edit Profile
        </button>
      </section>

      {/* ─── Danger Zone ─── */}
      <section className="glass-panel rounded-3xl p-8 space-y-4 border-error/20">
        <h3 className="text-sm font-bold tracking-widest uppercase text-error">Danger Zone</h3>
        <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          Logging out will end your current session. You&apos;ll need to sign in again to access your data.
        </p>
        <button className="interactive-btn px-5 py-2.5 rounded-xl bg-error/10 hover:bg-error/20 border border-error/20 text-error text-sm font-semibold tracking-wide transition-colors flex items-center gap-2">
          <LogOut size={16} /> Sign Out
        </button>
      </section>
    </div>
  );
}
