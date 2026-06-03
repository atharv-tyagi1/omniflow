'use client';

import React, { useState } from 'react';
import { X, User, Mail, Moon, Sun, Monitor, LogOut, Save, Check } from 'lucide-react';
import { useTheme, type Theme } from '@/context/ThemeContext';

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const themeOptions: { id: Theme; icon: React.ElementType; label: string }[] = [
  { id: 'dark',   icon: Moon,    label: 'Dark' },
  { id: 'light',  icon: Sun,     label: 'Light' },
  { id: 'system', icon: Monitor, label: 'System' },
];

export default function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const [username, setUsername] = useState('John Doe');
  const [email, setEmail] = useState('john.doe@example.com');
  const [saved, setSaved] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const { theme, setTheme, resolvedTheme } = useTheme();

  const handleSave = () => {
    setSaved(true);
    setIsEditing(false);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleLogout = () => {
    alert('You have been logged out.\n\n(Authentication integration pending)');
    setShowLogoutConfirm(false);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed top-0 right-0 h-full w-[380px] z-50 flex flex-col shadow-2xl"
        style={{
          background: 'var(--glass-bg-float)',
          backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)',
          borderLeft: '1px solid var(--surface-border)',
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b" style={{ borderColor: 'var(--surface-border)' }}>
          <h3 className="text-lg font-semibold tracking-wide" style={{ color: 'var(--text-primary)' }}>Settings</h3>
          <button
            className="p-2 rounded-xl transition-colors"
            style={{ color: 'var(--text-muted)' }}
            onClick={onClose}
            onMouseEnter={e => { e.currentTarget.style.background = 'var(--hover-bg)'; e.currentTarget.style.color = 'var(--text-primary)'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-muted)'; }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-8 custom-scrollbar">

          {/* ── Profile ── */}
          <section className="space-y-4">
            <div className="text-[10px] uppercase tracking-[0.15em] font-bold" style={{ color: 'var(--text-muted)' }}>Profile</div>

            {/* Avatar */}
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-accent-blue/10 border border-accent-blue/20 flex items-center justify-center text-accent-blue text-sm font-bold tracking-wider">
                {username.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)}
              </div>
              <div>
                <div className="text-sm font-semibold tracking-wide" style={{ color: 'var(--text-primary)' }}>{username}</div>
                <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Business Analyst</div>
              </div>
            </div>

            {/* Username field */}
            <div className="space-y-1.5">
              <label className="text-[11px] uppercase tracking-widest font-semibold" style={{ color: 'var(--text-muted)' }}>Username</label>
              <div className="flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200"
                style={{ background: 'var(--input-bg)', border: '1px solid var(--surface-border)' }}
              >
                <User size={16} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => { setUsername(e.target.value); setIsEditing(true); }}
                  className="bg-transparent border-none outline-none text-sm w-full"
                  style={{ color: 'var(--text-primary)' }}
                />
              </div>
            </div>

            {/* Email field */}
            <div className="space-y-1.5">
              <label className="text-[11px] uppercase tracking-widest font-semibold" style={{ color: 'var(--text-muted)' }}>Email</label>
              <div className="flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200"
                style={{ background: 'var(--input-bg)', border: '1px solid var(--surface-border)' }}
              >
                <Mail size={16} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); setIsEditing(true); }}
                  className="bg-transparent border-none outline-none text-sm w-full"
                  style={{ color: 'var(--text-primary)' }}
                />
              </div>
            </div>

            {/* Save button */}
            {isEditing && (
              <button
                className="interactive-btn flex items-center gap-2 px-4 py-2.5 rounded-xl bg-accent-blue text-white text-xs font-semibold tracking-wide hover:bg-accent-blue/90 transition-colors shadow-[0_0_15px_rgba(56,189,248,0.2)]"
                onClick={handleSave}
              >
                <Save size={14} /> Save Changes
              </button>
            )}
            {saved && (
              <div className="flex items-center gap-2 text-xs font-medium text-success animate-fade-in">
                <Check size={14} /> Changes saved successfully
              </div>
            )}
          </section>

          {/* ── Appearance / Theme ── */}
          <section className="space-y-4">
            <div className="text-[10px] uppercase tracking-[0.15em] font-bold" style={{ color: 'var(--text-muted)' }}>Appearance</div>

            <div className="space-y-2">
              <div className="text-xs font-medium mb-3" style={{ color: 'var(--text-secondary)' }}>Theme</div>
              <div className="grid grid-cols-3 gap-2 p-1 rounded-2xl" style={{ background: 'var(--input-bg)', border: '1px solid var(--surface-border)' }}>
                {themeOptions.map((opt) => {
                  const isActive = theme === opt.id;
                  return (
                    <button
                      key={opt.id}
                      onClick={() => setTheme(opt.id)}
                      className={`flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all duration-200 ${
                        isActive
                          ? 'bg-accent-blue text-white shadow-[0_0_15px_rgba(56,189,248,0.3)]'
                          : ''
                      }`}
                      style={!isActive ? { color: 'var(--text-muted)' } : undefined}
                      onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = 'var(--hover-bg)'; }}
                      onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = 'transparent'; }}
                    >
                      <opt.icon size={14} />
                      {opt.label}
                    </button>
                  );
                })}
              </div>
              <p className="text-[11px] mt-2" style={{ color: 'var(--text-muted)' }}>
                {theme === 'system'
                  ? `Currently using ${resolvedTheme} mode (from your OS).`
                  : `Using ${theme} mode.`
                }
              </p>
            </div>
          </section>

          {/* ── Session / Danger ── */}
          <section className="space-y-4 pt-4 border-t" style={{ borderColor: 'var(--surface-border)' }}>
            <div className="text-[10px] uppercase tracking-[0.15em] font-bold text-error">Session</div>
            {!showLogoutConfirm ? (
              <button
                className="interactive-btn flex items-center gap-2 px-4 py-2.5 rounded-xl bg-error/10 hover:bg-error/20 border border-error/20 text-error text-xs font-semibold tracking-wide transition-colors w-full justify-center"
                onClick={() => setShowLogoutConfirm(true)}
              >
                <LogOut size={16} /> Log Out
              </button>
            ) : (
              <div className="space-y-3 p-4 rounded-2xl border border-error/20 bg-error/5 animate-fade-in">
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Are you sure you want to log out?</p>
                <div className="flex gap-2">
                  <button
                    className="flex-1 py-2 rounded-xl text-xs font-semibold tracking-wide transition-colors"
                    style={{ background: 'var(--hover-bg)', border: '1px solid var(--surface-border)', color: 'var(--text-primary)' }}
                    onClick={() => setShowLogoutConfirm(false)}
                  >
                    Cancel
                  </button>
                  <button
                    className="flex-1 py-2 rounded-xl bg-error text-white text-xs font-semibold tracking-wide transition-colors hover:bg-error/90"
                    onClick={handleLogout}
                  >
                    Yes, Log Out
                  </button>
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </>
  );
}
