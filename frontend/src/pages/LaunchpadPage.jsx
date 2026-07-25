import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Users, Laptop, Headphones, TrendingUp, ShieldCheck, Cpu, Database, ArrowRight, ExternalLink, Activity, Lock } from 'lucide-react';
import { PORTALS } from '../config/portals';

const ICON_MAP = {
  Users: Users,
  Laptop: Laptop,
  Headphones: Headphones,
  TrendingUp: TrendingUp
};

const PORTAL_KEYS = ['hr', 'it', 'support', 'sales'];

export default function LaunchpadPage() {
  useEffect(() => {
    document.body.removeAttribute('data-portal');
  }, []);

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '40px 24px' }}>
      
      {/* Header Banner */}
      <div style={{ textAlign: 'center', marginBottom: '48px' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 16px', background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', borderRadius: '9999px', color: '#60a5fa', fontSize: '0.825rem', fontWeight: 600, marginBottom: '16px' }}>
          <ShieldCheck size={16} />
          <span>Unified Multi-Tenant Agentic RAG Gateway</span>
        </div>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#ffffff', marginBottom: '12px' }}>
          Enterprise Client Portal Suite
        </h1>
        <p style={{ fontSize: '1.05rem', color: '#9ca3af', maxWidth: '720px', margin: '0 auto', lineHeight: '1.6' }}>
          Select an enterprise portal below to launch its standalone AI assistant. Each portal connects to the central serving engine using isolated JWT claims, guaranteeing zero data leakage across tenant boundaries.
        </p>
      </div>

      {/* Grid of 4 Deployed Client Portals */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px', marginBottom: '56px' }}>
        {PORTAL_KEYS.map((key) => {
          const portal = PORTALS[key];
          const IconComponent = ICON_MAP[portal.iconName] || ShieldCheck;
          
          const glowMap = {
            hr: 'rgba(16, 185, 129, 0.2)',
            it: 'rgba(6, 182, 212, 0.2)',
            support: 'rgba(168, 85, 247, 0.2)',
            sales: 'rgba(245, 158, 11, 0.2)'
          };

          const colorMap = {
            hr: '#10b981',
            it: '#06b6d4',
            support: '#a855f7',
            sales: '#f59e0b'
          };

          return (
            <div
              key={key}
              className="glass-panel glass-panel-interactive"
              style={{
                padding: '28px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                position: 'relative',
                overflow: 'hidden'
              }}
            >
              <div>
                {/* Icon & Scope Badge */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
                  <div
                    style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '14px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: `linear-gradient(135deg, ${colorMap[key]}, ${colorMap[key]}dd)`,
                      color: '#ffffff',
                      boxShadow: `0 6px 20px ${glowMap[key]}`
                    }}
                  >
                    <IconComponent size={24} />
                  </div>
                  <span
                    style={{
                      padding: '4px 10px',
                      borderRadius: '9999px',
                      fontSize: '0.725rem',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      background: 'rgba(255, 255, 255, 0.06)',
                      border: '1px solid rgba(255, 255, 255, 0.12)',
                      color: colorMap[key]
                    }}
                  >
                    scope: {portal.scope}
                  </span>
                </div>

                {/* Portal Title & Info */}
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff', marginBottom: '6px' }}>
                  {portal.name}
                </h3>
                <p style={{ fontSize: '0.8rem', color: colorMap[key], fontWeight: 600, marginBottom: '14px' }}>
                  Role: <span style={{ color: '#d1d5db' }}>{portal.role}</span>
                </p>
                <p style={{ fontSize: '0.875rem', color: '#9ca3af', lineHeight: '1.5', marginBottom: '24px' }}>
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
                  padding: '12px 20px',
                  borderRadius: '12px',
                  background: `linear-gradient(135deg, ${colorMap[key]}, ${colorMap[key]}dd)`,
                  color: '#ffffff',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  textDecoration: 'none',
                  boxShadow: `0 4px 14px ${glowMap[key]}`,
                  transition: 'all 0.2s'
                }}
              >
                <span>Launch {portal.name.split(' ')[0]} App</span>
                <ArrowRight size={16} />
              </Link>
            </div>
          );
        })}
      </div>

      {/* Gateway Architecture Stats Banner */}
      <div className="glass-panel" style={{ padding: '32px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: 'rgba(59, 130, 246, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#60a5fa' }}>
            <Cpu size={20} />
          </div>
          <div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff' }}>LangGraph StateGraph</div>
            <div style={{ fontSize: '0.8rem', color: '#9ca3af' }}>Self-Correcting Routing Engine</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#34d399' }}>
            <Database size={20} />
          </div>
          <div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff' }}>Hybrid RRF Search</div>
            <div style={{ fontSize: '0.8rem', color: '#9ca3af' }}>pgvector + BM25 Sparse Index</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: 'rgba(168, 85, 247, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#c084fc' }}>
            <Activity size={20} />
          </div>
          <div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff' }}>SSE Real-Time Stream</div>
            <div style={{ fontSize: '0.8rem', color: '#9ca3af' }}>Token-by-Token Generator</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: 'rgba(245, 158, 11, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fbbf24' }}>
            <Lock size={20} />
          </div>
          <div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff' }}>Strict JWT Boundaries</div>
            <div style={{ fontSize: '0.8rem', color: '#9ca3af' }}>Multi-Tenant Context Enforcement</div>
          </div>
        </div>
      </div>

    </div>
  );
}
