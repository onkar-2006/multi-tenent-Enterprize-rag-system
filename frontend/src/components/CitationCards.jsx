import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, BookOpen, ExternalLink, ShieldCheck } from 'lucide-react';

export default function CitationCards({ references, scope }) {
  const [isOpen, setIsOpen] = useState(true);

  if (!references || references.length === 0) return null;

  return (
    <div style={{ marginTop: '12px', borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '12px' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          width: '100%',
          background: 'none',
          border: 'none',
          color: 'var(--text-muted)',
          fontSize: '0.8rem',
          fontWeight: 600,
          cursor: 'pointer',
          padding: '4px 0'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <BookOpen size={14} style={{ color: 'var(--portal-accent)' }} />
          <span>Retrieved Document Context ({references.length} Sources Scoped to '{scope}')</span>
        </div>
        {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {isOpen && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '10px', marginTop: '8px' }}>
          {references.map((ref, idx) => (
            <div
              key={idx}
              style={{
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                borderRadius: '8px',
                padding: '10px 12px',
                fontSize: '0.775rem'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600, color: '#f3f4f6', marginBottom: '4px' }}>
                <FileText size={13} style={{ color: 'var(--portal-accent)', flexShrink: 0 }} />
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {ref.source}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#9ca3af', fontSize: '0.725rem' }}>
                <span>Page {ref.page}</span>
                <span style={{ color: '#10b981', fontFamily: 'var(--font-mono)' }}>RRF Score: {ref.rrf_score}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
