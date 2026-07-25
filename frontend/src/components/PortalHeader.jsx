import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Users, Laptop, Headphones, TrendingUp, Key, ArrowLeft, Shield, CheckCircle2, Activity } from 'lucide-react';
import { parseJwt } from '../services/tokenService';

const ICON_MAP = {
  Users: Users,
  Laptop: Laptop,
  Headphones: Headphones,
  TrendingUp: TrendingUp
};

export default function PortalHeader({ portalConfig, token }) {
  const [showJwtInspector, setShowJwtInspector] = useState(false);
  const IconComponent = ICON_MAP[portalConfig.iconName] || Shield;
  const claims = token ? parseJwt(token) : null;

  return (
    <header className="glass-panel" style={{ borderRadius: '0 0 16px 16px', borderTop: 'none', padding: '16px 28px', marginBottom: '24px' }}>
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
              width: '38px', 
              height: '38px', 
              borderRadius: '10px', 
              background: 'rgba(255,255,255,0.05)', 
              color: '#9ca3af',
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
            width: '44px',
            height: '44px',
            borderRadius: '12px',
            background: 'var(--portal-gradient)',
            color: '#ffffff',
            boxShadow: '0 4px 20px var(--portal-glow)'
          }}>
            <IconComponent size={22} />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.01em', color: '#ffffff' }}>
                {portalConfig.name}
              </h1>
              <span className="badge badge-portal">
                <Shield size={12} /> {portalConfig.scope}
              </span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              {portalConfig.company} • Multi-Tenant Enterprise Gateway
            </p>
          </div>
        </div>

        {/* Right: Security Claims Badge & Launchpad Link */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Status Indicator */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: '9999px', fontSize: '0.8rem', color: '#10b981' }}>
            <span className="status-dot"></span>
            <span>Gateway Active</span>
          </div>

          {/* JWT Inspector Trigger */}
          <button
            onClick={() => setShowJwtInspector(!showJwtInspector)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              borderRadius: '10px',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-color)',
              color: '#d1d5db',
              fontSize: '0.825rem',
              fontWeight: 500,
              cursor: 'pointer',
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
        <div style={{ marginTop: '16px', padding: '14px 18px', background: 'rgba(15, 23, 42, 0.95)', border: '1px solid var(--portal-border)', borderRadius: '12px', fontSize: '0.85rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px', color: 'var(--portal-accent)', fontWeight: 600 }}>
            <span><Shield size={14} style={{ inlineSize: '14px' }} /> Active Security JWT Context</span>
            <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Verified by FastAPI Security Gateway</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px', fontFamily: 'var(--font-mono)' }}>
            <div>
              <span style={{ color: '#6b7280', fontSize: '0.75rem' }}>SCOPE:</span>
              <div style={{ color: '#10b981', fontWeight: 600 }}>"{claims.scope}"</div>
            </div>
            <div>
              <span style={{ color: '#6b7280', fontSize: '0.75rem' }}>ROLE:</span>
              <div style={{ color: '#06b6d4', fontWeight: 600 }}>"{claims.role}"</div>
            </div>
            <div>
              <span style={{ color: '#6b7280', fontSize: '0.75rem' }}>USER_ID:</span>
              <div style={{ color: '#f59e0b', fontWeight: 600 }}>"{claims.user_id || 'anonymous'}"</div>
            </div>
            <div>
              <span style={{ color: '#6b7280', fontSize: '0.75rem' }}>ISOLATION:</span>
              <div style={{ color: '#a855f7', fontWeight: 600 }}>Strict Tenant Bound</div>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
