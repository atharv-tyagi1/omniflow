"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { Mail, Lock, ArrowRight, Loader2, Command } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const router = useRouter();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const res = await api.post<any>('/api/v1/auth/login', { email, password });
      if (res && res.data) {
        login(res.data.access_token, res.data.user);
        router.push('/');
      }
    } catch (err: any) {
      setError(err.message || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-background relative overflow-hidden">
      
      {/* Background System */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[20%] left-[20%] w-[40%] h-[40%] rounded-full bg-accent-blue opacity-[0.05] blur-[120px]"></div>
        <div className="absolute bottom-[20%] right-[20%] w-[40%] h-[40%] rounded-full bg-accent-purple opacity-[0.05] blur-[120px]"></div>
      </div>

      <div className="z-10 w-full max-w-[420px] p-6">
        <div className="flex flex-col items-center mb-8">
          <div className="h-12 w-12 rounded-2xl bg-accent-blue/10 text-accent-blue flex items-center justify-center mb-4 border border-accent-blue/20">
            <Command className="h-6 w-6" />
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-primary-text">Welcome back</h1>
          <p className="text-sm text-secondary-text mt-2">Sign in to your OmniFlow workspace</p>
        </div>

        <form onSubmit={handleSubmit} className="glass-panel p-8 rounded-3xl space-y-5 relative overflow-hidden">
          {error && (
            <div className="bg-error/10 text-error text-sm font-medium px-4 py-3 rounded-xl border border-error/20 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-error" />
              {error}
            </div>
          )}
          
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium tracking-wide text-secondary-text uppercase">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-text" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-hover-bg border border-surface-border rounded-xl py-2.5 pl-10 pr-4 text-sm text-primary-text placeholder:text-muted-text focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50 transition-all"
                  placeholder="name@company.com"
                  required
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium tracking-wide text-secondary-text uppercase">Password</label>
                <Link href="#" className="text-xs font-medium text-accent-blue hover:text-accent-purple transition-colors">
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-text" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-hover-bg border border-surface-border rounded-xl py-2.5 pl-10 pr-4 text-sm text-primary-text placeholder:text-muted-text focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50 transition-all"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-primary-text text-background font-medium py-3 rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 mt-4"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Sign In'}
            {!loading && <ArrowRight className="h-4 w-4" />}
          </button>
        </form>

        <p className="text-center text-sm text-secondary-text mt-8">
          Don't have an account?{' '}
          <Link href="/signup" className="text-accent-blue font-medium hover:text-accent-purple transition-colors">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
