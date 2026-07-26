import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Users, Laptop, Headphones, TrendingUp, Key, ArrowLeft, Shield, Sun, Moon } from 'lucide-react';
import { parseJwt } from '../services/tokenService';

const ICON_MAP = {
  Users: Users,
  Laptop: Laptop,
  Headphones: Headphones,
  TrendingUp: TrendingUp
};

export default function PortalHeader({ portalConfig, token }) {
  const [showJwtInspector, setShowJwtInspector] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('app-theme') || 'light');
  
  const IconComponent = ICON_MAP[portalConfig.iconName] || Shield;
  const claims = token ? parseJwt(token) : null;

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
    <header className="glass-panel" style={{ borderRadius: '24px', padding: '16px 28px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        
        {/* Left: Portal Identity */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <Link 
            to="/" 
            title="Return to Central Launchpad"
            style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              width: '40px', 
              height: '40px', 
              borderRadius: '9999px', 
              background: 'var(--portal-bg-subtle)', 
              color: 'var(--text-muted)',
              border: '1px solid var(--border-color)',
              textDecoration: 'none',
              transition: 'all 0.2s'
            }}
          >
            <ArrowLeft size={18} />
          </Link>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '46px',
            height: '46px',
            borderRadius: '16px',
            background: 'var(--portal-gradient)',
            color: '#ffffff',
            boxShadow: '0 6px 20px var(--portal-glow)'
          }}>
            <IconComponent size={22} />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.01em', color: 'var(--text-main)' }}>
                {portalConfig.name}
              </h1>
              <span className="badge badge-portal">
                <Shield size={12} /> {portalConfig.scope}
              </span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: '2px', fontWeight: 500 }}>
              {portalConfig.company} • Multi-Tenant Enterprise Gateway
            </p>
          </div>
        </div>

        {/* Right: Controls & Security */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Status Indicator */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 14px', background: 'var(--portal-bg-subtle)', border: '1px solid var(--portal-border)', borderRadius: '9999px', fontSize: '0.8rem', color: 'var(--portal-text)', fontWeight: 600 }}>
            <span className="status-dot"></span>
            <span>Gateway Active</span>
          </div>

          {/* Theme Toggle Button (Sun / Moon) */}
          <button
            onClick={toggleTheme}
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '38px',
              height: '38px',
              borderRadius: '9999px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-main)',
              cursor: 'pointer',
              boxShadow: 'var(--shadow-sm)',
              transition: 'all 0.2s'
            }}
          >
            {theme === 'dark' ? <Sun size={16} style={{ color: '#fbbf24' }} /> : <Moon size={16} style={{ color: '#6366f1' }} />}
          </button>

          {/* JWT Inspector Trigger */}
          <button
            onClick={() => setShowJwtInspector(!showJwtInspector)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '9999px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-main)',
              fontSize: '0.825rem',
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: 'var(--shadow-sm)',
              transition: 'all 0.2s'
            }}
          >
            <Key size={14} style={{ color: 'var(--portal-accent)' }} />
            <span>JWT Claims</span>
          </button>
        </div>

      </div>

      {/* JWT Claims Modal/Popover */}
      {showJwtInspector && claims && (
        <div style={{ marginTop: '16px', padding: '16px 20px', background: 'var(--bg-card)', border: '1px solid var(--portal-border)', borderRadius: '18px', fontSize: '0.85rem', boxShadow: 'var(--shadow-lg)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px', color: 'var(--portal-text)', fontWeight: 700 }}>
            <span><Shield size={14} style={{ display: 'inline', marginRight: '6px' }} /> Active Security JWT Context</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Verified by FastAPI Security Gateway</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px', fontFamily: 'var(--font-mono)' }}>
            <div style={{ background: 'var(--portal-bg-subtle)', padding: '8px 12px', borderRadius: '10px' }}>
              <span style={{ color: 'var(--text-dim)', fontSize: '0.7rem', display: 'block', fontWeight: 600 }}>SCOPE</span>
              <div style={{ color: 'var(--portal-text)', fontWeight: 700 }}>"{claims.scope}"</div>
            </div>
            <div style={{ background: 'var(--portal-bg-subtle)', padding: '8px 12px', borderRadius: '10px' }}>
              <span style={{ color: 'var(--text-dim)', fontSize: '0.7rem', display: 'block', fontWeight: 600 }}>ROLE</span>
              <div style={{ color: 'var(--portal-accent)', fontWeight: 700 }}>"{claims.role}"</div>
            </div>
            <div style={{ background: 'var(--portal-bg-subtle)', padding: '8px 12px', borderRadius: '10px' }}>
              <span style={{ color: 'var(--text-dim)', fontSize: '0.7rem', display: 'block', fontWeight: 600 }}>USER_ID</span>
              <div style={{ color: 'var(--portal-accent)', fontWeight: 700 }}>"{claims.user_id || 'anonymous'}"</div>
            </div>
            <div style={{ background: 'var(--portal-bg-subtle)', padding: '8px 12px', borderRadius: '10px' }}>
              <span style={{ color: 'var(--text-dim)', fontSize: '0.7rem', display: 'block', fontWeight: 600 }}>ISOLATION</span>
              <div style={{ color: 'var(--portal-text)', fontWeight: 700 }}>Tenant Bound</div>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
