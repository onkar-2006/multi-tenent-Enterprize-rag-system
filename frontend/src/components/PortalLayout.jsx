import React, { useEffect, useState } from 'react';
import PortalHeader from './PortalHeader';
import ChatInterface from './ChatInterface';
import { PORTALS } from '../config/portals';
import { fetchPortalTokens } from '../services/tokenService';

export default function PortalLayout({ portalKey }) {
  const portalConfig = PORTALS[portalKey];
  const [tokens, setTokens] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Set data-portal attribute on body for CSS domain theme variables
    document.body.setAttribute('data-portal', portalConfig.colorTheme);

    fetchPortalTokens().then(data => {
      setTokens(data);
      setLoading(false);
    });
  }, [portalKey, portalConfig]);

  const activeToken = tokens ? tokens[portalKey] : '';

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', color: '#9ca3af', fontSize: '0.9rem' }}>
        <span>Connecting to Multi-Tenant Gateway Security Context...</span>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 20px 40px 20px' }}>
      <PortalHeader portalConfig={portalConfig} token={activeToken} />
      <ChatInterface portalConfig={portalConfig} token={activeToken} />
    </div>
  );
}
