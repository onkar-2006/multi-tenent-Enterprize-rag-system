import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, BookOpen } from 'lucide-react';

export default function CitationCards({ references, scope }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!references || references.length === 0) return null;

  return (
    <div style={{ marginTop: '12px', borderTop: '1px solid var(--border-color)', paddingTop: '12px' }}>
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
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '10px', marginTop: '10px' }}>
          {references.map((ref, idx) => (
            <div
              key={idx}
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-color)',
                borderRadius: '14px',
                padding: '12px 14px',
                fontSize: '0.775rem',
                boxShadow: 'var(--shadow-sm)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, color: 'var(--text-main)', marginBottom: '6px' }}>
                <FileText size={14} style={{ color: 'var(--portal-accent)', flexShrink: 0 }} />
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {ref.source}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-dim)', fontSize: '0.725rem' }}>
                <span>Page {ref.page}</span>
                <span style={{ color: 'var(--portal-accent)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>RRF Score: {ref.rrf_score}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
