import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send, Bot, User, RefreshCw, Sparkles, MessageSquare } from 'lucide-react';
import CitationCards from './CitationCards';
import { API_BASE_URL } from '../config/portals';

export default function ChatInterface({ portalConfig, token }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: `Hello! Welcome to the **${portalConfig.name}**. I am your dedicated AI Assistant scoped strictly to **\`${portalConfig.scope}\`** enterprise documentation and authorized tools. How can I help you today?`,
      references: []
    }
  ]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [threadId, setThreadId] = useState(`thread-${portalConfig.id}-${Date.now().toString().slice(-4)}`);
  const chatBottomRef = useRef(null);

  useEffect(() => {
    setMessages([
      {
        id: 'welcome',
        sender: 'assistant',
        text: `Hello! Welcome to the **${portalConfig.name}**. I am your dedicated AI Assistant scoped strictly to **\`${portalConfig.scope}\`** enterprise documentation and authorized tools. How can I help you today?`,
        references: []
      }
    ]);
    setThreadId(`thread-${portalConfig.id}-${Date.now().toString().slice(-4)}`);
  }, [portalConfig]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const handleSend = async (textToSend) => {
    const prompt = textToSend || input;
    if (!prompt.trim() || isStreaming) return;

    if (!textToSend) setInput('');

    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `assistant-${Date.now()}`;

    setMessages(prev => [
      ...prev,
      { id: userMsgId, sender: 'user', text: prompt },
      { id: assistantMsgId, sender: 'assistant', text: '', isStreaming: true, references: [] }
    ]);

    setIsStreaming(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message: prompt,
          thread_id: threadId
        })
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let streamedText = '';
      let references = [];
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data: ')) {
            const dataStr = trimmed.slice(6);
            try {
              const data = JSON.parse(dataStr);
              if (data.token) {
                streamedText += data.token;
                setMessages(prev =>
                  prev.map(msg =>
                    msg.id === assistantMsgId
                      ? { ...msg, text: streamedText }
                      : msg
                  )
                );
              }
              if (data.references) {
                references = data.references;
                setMessages(prev =>
                  prev.map(msg =>
                    msg.id === assistantMsgId
                      ? { ...msg, references: references }
                      : msg
                  )
                );
              }
            } catch (e) {
              // Ignore invalid JSON chunks
            }
          }
        }
      }

      setMessages(prev =>
        prev.map(msg =>
          msg.id === assistantMsgId
            ? { ...msg, isStreaming: false }
            : msg
        )
      );

    } catch (err) {
      console.error('Streaming error:', err);
      setMessages(prev =>
        prev.map(msg =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                text: `⚠️ **Connection Error**: Could not connect to the serving engine (${err.message}). Make sure the FastAPI server is running on \`http://127.0.0.1:8000\`.`,
                isStreaming: false
              }
            : msg
        )
      );
    } finally {
      setIsStreaming(false);
    }
  };

  const handleNewThread = () => {
    setThreadId(`thread-${portalConfig.id}-${Date.now().toString().slice(-4)}`);
    setMessages([
      {
        id: 'welcome',
        sender: 'assistant',
        text: `New conversation thread initialized (\`${threadId}\`). How can I assist you?`,
        references: []
      }
    ]);
  };

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 160px)', minHeight: '540px', borderRadius: '28px', overflow: 'hidden' }}>
      
      {/* Top Session Control Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 24px', borderBottom: '1px solid var(--border-color)', background: 'var(--bg-card)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <MessageSquare size={15} style={{ color: 'var(--portal-accent)' }} />
          <span>Active Session Thread: <strong style={{ color: 'var(--text-main)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{threadId}</strong></span>
        </div>
        <button
          onClick={handleNewThread}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-color)',
            borderRadius: '9999px',
            color: 'var(--text-main)',
            padding: '5px 14px',
            fontSize: '0.775rem',
            fontWeight: 600,
            cursor: 'pointer',
            boxShadow: 'var(--shadow-sm)',
            transition: 'all 0.2s'
          }}
        >
          <RefreshCw size={12} /> New Session
        </button>
      </div>

      {/* Messages Feed */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '28px', display: 'flex', flexDirection: 'column', gap: '22px', background: 'var(--bg-surface)' }}>
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              display: 'flex',
              gap: '14px',
              maxWidth: msg.sender === 'user' ? '82%' : '100%',
              alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              flexDirection: msg.sender === 'user' ? 'row-reverse' : 'row'
            }}
          >
            {/* Avatar */}
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '14px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                background: msg.sender === 'user' ? 'linear-gradient(135deg, #2563eb, #3b82f6)' : 'var(--portal-gradient)',
                color: '#ffffff',
                boxShadow: msg.sender === 'user' ? '0 4px 14px rgba(37, 99, 235, 0.25)' : '0 4px 14px var(--portal-glow)'
              }}
            >
              {msg.sender === 'user' ? <User size={18} /> : <Bot size={18} />}
            </div>

            {/* Rounded Message Bubble */}
            <div style={{ flex: 1, maxWidth: '850px' }}>
              <div
                style={{
                  background: msg.sender === 'user' ? 'var(--portal-gradient)' : 'var(--bg-card)',
                  color: msg.sender === 'user' ? '#ffffff' : 'var(--text-main)',
                  border: msg.sender === 'user' ? 'none' : '1px solid var(--border-color)',
                  borderRadius: msg.sender === 'user' ? '22px 22px 4px 22px' : '22px 22px 22px 4px',
                  padding: '16px 22px',
                  fontSize: '0.925rem',
                  lineHeight: '1.6',
                  boxShadow: msg.sender === 'user' ? '0 6px 20px var(--portal-glow)' : 'var(--shadow-sm)'
                }}
              >
                <div className="markdown-content">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.text || (msg.isStreaming ? 'Thinking & retrieving scoped documents...' : '')}
                  </ReactMarkdown>
                </div>
                {msg.isStreaming && <span className="streaming-cursor"></span>}
              </div>

              {/* Document Citations */}
              {msg.references && msg.references.length > 0 && (
                <CitationCards references={msg.references} scope={portalConfig.scope} />
              )}
            </div>
          </div>
        ))}
        <div ref={chatBottomRef} />
      </div>

      {/* Suggested Prompts (Pill Badges) */}
      {messages.length <= 2 && (
        <div style={{ padding: '8px 24px 14px 24px', display: 'flex', gap: '8px', flexWrap: 'wrap', background: 'var(--bg-card)', borderTop: '1px solid var(--border-color)' }}>
          {portalConfig.suggestedPrompts.map((promptText, i) => (
            <button
              key={i}
              onClick={() => handleSend(promptText)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                borderRadius: '9999px',
                background: 'var(--portal-bg-subtle)',
                border: '1px solid var(--portal-border)',
                color: 'var(--portal-text)',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              <Sparkles size={13} style={{ color: 'var(--portal-accent)' }} />
              <span>{promptText}</span>
            </button>
          ))}
        </div>
      )}

      {/* Input Box (Rounded Pill Shape) */}
      <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border-color)', background: 'var(--bg-card)' }}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          style={{ display: 'flex', gap: '12px' }}
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask ${portalConfig.name} (${portalConfig.scope} scope)...`}
            disabled={isStreaming}
            style={{
              flex: 1,
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-color)',
              borderRadius: '9999px',
              padding: '14px 24px',
              color: 'var(--text-main)',
              fontSize: '0.925rem',
              outline: 'none',
              transition: 'all 0.2s'
            }}
          />
          <button
            type="submit"
            disabled={isStreaming || !input.trim()}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '48px',
              height: '48px',
              borderRadius: '9999px',
              background: 'var(--portal-gradient)',
              border: 'none',
              color: '#ffffff',
              cursor: isStreaming || !input.trim() ? 'not-allowed' : 'pointer',
              opacity: isStreaming || !input.trim() ? 0.5 : 1,
              boxShadow: '0 6px 18px var(--portal-glow)',
              transition: 'all 0.2s'
            }}
          >
            <Send size={18} />
          </button>
        </form>
      </div>

    </div>
  );
}
