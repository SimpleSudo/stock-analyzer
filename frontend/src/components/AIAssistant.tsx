import React, { useState, useRef, useEffect, useCallback } from 'react';
import type { StockAnalysisResponse } from '../utils/types';
import { streamAIChat, aiChat } from '../services/api';

interface AIAssistantProps {
  analysis: StockAnalysisResponse | null;
  show: boolean;
  onClose: () => void;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  streaming?: boolean;
}

const AIAssistant: React.FC<AIAssistantProps> = ({ analysis, show, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (analysis) {
      setMessages([{
        role: 'assistant',
        content: `我是 AI 分析助手，正在分析 **${analysis.name || analysis.symbol}**。\n\n当前信号：${analysis.signal}（评分 ${analysis.score}）\n\n有什么想了解的？您可以问我关于这只股票的技术面、基本面、操作建议等问题。`
      }]);
    }
  }, [analysis?.symbol]);

  const buildContext = useCallback(() => {
    if (!analysis) return undefined;
    return {
      signal: analysis.signal,
      score: analysis.score,
      reasons: analysis.reasons,
      indicators: analysis.indicators,
      fundamental: analysis.fundamental,
      price: analysis.data?.latest?.price,
      change_pct: analysis.data?.latest?.change_pct,
    };
  }, [analysis]);

  if (!show || !analysis) return null;

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    const context = buildContext();

    // 先尝试 SSE 流式，失败降级到普通请求
    const assistantIdx = messages.length + 1; // +1 for user msg just added
    setMessages(prev => [...prev, { role: 'assistant', content: '', streaming: true }]);

    try {
      await streamAIChat(
        userMsg,
        (token) => {
          setMessages(prev => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last?.role === 'assistant') {
              updated[updated.length - 1] = { ...last, content: last.content + token };
            }
            return updated;
          });
        },
        () => {
          setMessages(prev => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last?.role === 'assistant') {
              updated[updated.length - 1] = { ...last, streaming: false };
            }
            return updated;
          });
          setLoading(false);
        },
        async (err) => {
          // SSE 失败，降级到普通请求
          try {
            const reply = await aiChat(userMsg, analysis.symbol, context);
            setMessages(prev => {
              const updated = [...prev];
              updated[updated.length - 1] = { role: 'assistant', content: reply };
              return updated;
            });
          } catch {
            setMessages(prev => {
              const updated = [...prev];
              updated[updated.length - 1] = {
                role: 'assistant',
                content: '抱歉，AI 回答暂时不可用，请稍后再试。',
              };
              return updated;
            });
          }
          setLoading(false);
        },
        analysis.symbol,
        context,
      );
    } catch {
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: 'assistant',
          content: '抱歉，AI 回答暂时不可用，请稍后再试。',
        };
        return updated;
      });
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="ai-assistant-backdrop" onClick={onClose}>
      <div className="ai-assistant-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '520px', display: 'flex', flexDirection: 'column', maxHeight: '80vh' }}>
        <div className="ai-assistant-header">
          <h3>🤖 AI 分析助手</h3>
          <button className="ai-assistant-close" onClick={onClose}>×</button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px', minHeight: '200px' }}>
          {messages.map((msg, i) => (
            <div key={i} style={{
              marginBottom: '12px',
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            }}>
              <div style={{
                maxWidth: '85%',
                padding: '10px 14px',
                borderRadius: msg.role === 'user' ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                background: msg.role === 'user' ? '#1a73e8' : 'var(--bg-secondary)',
                color: msg.role === 'user' ? '#fff' : 'var(--text-primary)',
                fontSize: '14px',
                lineHeight: '1.6',
                whiteSpace: 'pre-wrap',
              }}>
                {msg.content}
                {msg.streaming && <span className="typing-cursor">▊</span>}
              </div>
            </div>
          ))}
          {loading && messages[messages.length - 1]?.content === '' && (
            <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '12px' }}>
              <div style={{
                padding: '10px 14px', borderRadius: '14px 14px 14px 4px',
                background: 'var(--bg-secondary)', color: 'var(--text-secondary)', fontSize: '14px',
              }}>
                思考中...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div style={{
          padding: '12px 16px',
          borderTop: '1px solid var(--border-color)',
          display: 'flex', gap: '8px',
        }}>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入问题..."
            disabled={loading}
            style={{
              flex: 1, padding: '10px 12px', borderRadius: '8px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-primary)', color: 'var(--text-primary)',
              fontSize: '14px', outline: 'none',
            }}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            style={{
              padding: '10px 16px', borderRadius: '8px',
              background: '#1a73e8', color: '#fff', border: 'none',
              cursor: 'pointer', fontSize: '14px',
              opacity: loading || !input.trim() ? 0.5 : 1,
            }}
          >
            发送
          </button>
        </div>

        <div className="ai-assistant-footer">
          <p className="ai-disclaimer">
            AI 助手基于技术/基本面数据提供分析，不构成投资建议。
          </p>
        </div>
      </div>
    </div>
  );
};

export default AIAssistant;
