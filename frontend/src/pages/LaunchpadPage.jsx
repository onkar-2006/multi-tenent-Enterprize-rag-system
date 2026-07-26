import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Users, Laptop, Headphones, TrendingUp, ShieldCheck, Cpu, Database, ArrowRight, Lock, Activity, Sun, Moon } from 'lucide-react';
import { PORTALS } from '../config/portals';

const ICON_MAP = {
  Users: Users,
  Laptop: Laptop,
  Headphones: Headphones,
  TrendingUp: TrendingUp
};

const PORTAL_KEYS = ['hr', 'it', 'support', 'sales'];

export default function LaunchpadPage() {
  const [theme, setTheme] = useState(() => localStorage.getItem('app-theme') || 'light');

  useEffect(() => {
    document.body.removeAttribute('data-portal');
  }, []);

  useEffect(() => {
    if (theme === 'dark') {
      document.body.setAttribute('data-theme', 'dark');
    } else {
      document.body.removeAttribute('data-theme');
    }
    localStorage.setItem('app-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '48px 24px' }}>
      
      {/* Top Controls Bar */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '20px' }}>
        <button
          onClick={toggleTheme}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            borderRadius: '9999px',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            color: 'var(--text-main)',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: 'pointer',
            boxShadow: 'var(--shadow-sm)',
            transition: 'all 0.2s'
          }}
        >
          {theme === 'dark' ? (
            <>
              <Sun size={16} style={{ color: '#fbbf24' }} />
              <span>Light Mode</span>
            </>
          ) : (
            <>
              <Moon size={16} style={{ color: '#6366f1' }} />
              <span>Dark Mode</span>
            </>
          )}
        </button>
      </div>

      {/* Header Banner */}
      <div style={{ textAlign: 'center', marginBottom: '52px' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 18px', background: 'var(--portal-bg-subtle, #eff6ff)', border: '1px solid var(--portal-border, #bfdbfe)', borderRadius: '9999px', color: 'var(--accent-primary, #1d4ed8)', fontSize: '0.825rem', fontWeight: 700, marginBottom: '18px' }}>
          <ShieldCheck size={16} />
          <span>Unified Multi-Tenant Agentic RAG Gateway</span>
        </div>
        <h1 style={{ fontSize: '2.75rem', fontWeight: 800, letterSpacing: '-0.025em', color: 'var(--text-main)', marginBottom: '14px' }}>
          Enterprise Client Portal Suite
        </h1>
        <p style={{ fontSize: '1.05rem', color: 'var(--text-muted)', maxWidth: '720px', margin: '0 auto', lineHeight: '1.6', fontWeight: 500 }}>
          Select an enterprise portal below to launch its standalone AI assistant. Each portal connects to the central serving engine using isolated JWT claims, guaranteeing zero data leakage across tenant boundaries.
        </p>
      </div>

      {/* Grid of 4 Deployed Client Portals */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '28px', marginBottom: '60px' }}>
        {PORTAL_KEYS.map((key) => {
          const portal = PORTALS[key];
          const IconComponent = ICON_MAP[portal.iconName] || ShieldCheck;
          
          const colorMap = {
            hr: '#059669',
            it: '#2563eb',
            support: '#7c3aed',
            sales: '#d97706'
          };

          return (
            <div
              key={key}
              className="glass-panel glass-panel-interactive"
              style={{
                padding: '32px',
                borderRadius: '28px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                position: 'relative',
                overflow: 'hidden'
              }}
            >
              <div>
                {/* Icon & Scope Badge */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '22px' }}>
                  <div
                    style={{
                      width: '52px',
                      height: '52px',
                      borderRadius: '18px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: `linear-gradient(135deg, ${colorMap[key]}, ${colorMap[key]}dd)`,
                      color: '#ffffff',
                      boxShadow: `0 8px 22px rgba(0,0,0,0.12)`
                    }}
                  >
                    <IconComponent size={26} />
                  </div>
                  <span
                    style={{
                      padding: '5px 12px',
                      borderRadius: '9999px',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      background: 'var(--bg-dark)',
                      border: '1px solid var(--border-color)',
                      color: colorMap[key]
                    }}
                  >
                    scope: {portal.scope}
                  </span>
                </div>

                {/* Portal Title & Info */}
                <h3 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '6px', letterSpacing: '-0.01em' }}>
                  {portal.name}
                </h3>
                <p style={{ fontSize: '0.825rem', color: colorMap[key], fontWeight: 700, marginBottom: '16px' }}>
                  Role: <span style={{ color: 'var(--text-muted)' }}>{portal.role}</span>
                </p>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: '1.6', marginBottom: '28px', fontWeight: 500 }}>
                  {portal.description}
                </p>
              </div>

              {/* Launch Button */}
              <Link
                to={`/${key}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '14px 24px',
                  borderRadius: '9999px',
                  background: `linear-gradient(135deg, ${colorMap[key]}, ${colorMap[key]}dd)`,
                  color: '#ffffff',
                  fontWeight: 700,
                  fontSize: '0.925rem',
                  textDecoration: 'none',
                  boxShadow: `0 6px 18px rgba(0,0,0,0.12)`,
                  transition: 'all 0.2s'
                }}
              >
                <span>Launch {portal.name.split(' ')[0]} App</span>
                <ArrowRight size={17} />
              </Link>
            </div>
          );
        })}
      </div>

    </div>
  );
}
