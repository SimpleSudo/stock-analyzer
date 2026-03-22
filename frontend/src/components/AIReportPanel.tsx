import React, { useState } from 'react';

interface Props {
  report: string;
}

/**
 * 轻量级 Markdown 渲染：支持 ### 标题、**粗体**、- 列表项
 * 无需依赖 react-markdown，避免引入额外依赖
 */
const renderMarkdown = (text: string): React.ReactNode[] => {
  const nodes: React.ReactNode[] = [];

  text.split('\n').forEach((line, lineIdx) => {
    const key = lineIdx;

    // ### h3 标题
    if (line.startsWith('### ')) {
      nodes.push(
        <h4 key={key} style={{ margin: '18px 0 6px', fontSize: '15px', fontWeight: 700, color: 'var(--text-primary, #222)' }}>
          {renderInline(line.slice(4))}
        </h4>
      );
      return;
    }
    // ## h2 标题
    if (line.startsWith('## ')) {
      nodes.push(
        <h3 key={key} style={{ margin: '20px 0 8px', fontSize: '16px', fontWeight: 700, color: 'var(--text-primary, #222)' }}>
          {renderInline(line.slice(3))}
        </h3>
      );
      return;
    }
    // # h1 标题
    if (line.startsWith('# ')) {
      nodes.push(
        <h2 key={key} style={{ margin: '20px 0 8px', fontSize: '18px', fontWeight: 700 }}>
          {renderInline(line.slice(2))}
        </h2>
      );
      return;
    }
    // 分隔线
    if (line.trim() === '---' || line.trim() === '***') {
      nodes.push(<hr key={key} style={{ border: 'none', borderTop: '1px solid var(--border-color, #eee)', margin: '12px 0' }} />);
      return;
    }
    // 列表项（- 或 * 开头）
    if (/^[\-\*] /.test(line)) {
      nodes.push(
        <div key={key} style={{ display: 'flex', gap: '8px', margin: '4px 0', paddingLeft: '8px' }}>
          <span style={{ color: '#1a73e8', flexShrink: 0 }}>•</span>
          <span style={{ lineHeight: '1.6' }}>{renderInline(line.slice(2))}</span>
        </div>
      );
      return;
    }
    // 空行
    if (!line.trim()) {
      nodes.push(<div key={key} style={{ height: '6px' }} />);
      return;
    }
    // 普通段落
    nodes.push(
      <p key={key} style={{ margin: '4px 0', lineHeight: '1.7' }}>
        {renderInline(line)}
      </p>
    );
  });

  return nodes;
};

/** 行内格式：**粗体** */
const renderInline = (text: string): React.ReactNode[] => {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} style={{ fontWeight: 700 }}>{part.slice(2, -2)}</strong>;
    }
    return <React.Fragment key={i}>{part}</React.Fragment>;
  });
};

const AIReportPanel: React.FC<Props> = ({ report }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="metric-card" style={{ gridColumn: '1 / -1', padding: '0', overflow: 'hidden' }}>
      {/* 折叠头部 */}
      <button
        onClick={() => setExpanded(prev => !prev)}
        style={{
          width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '16px 20px', background: 'transparent', border: 'none',
          cursor: 'pointer', color: 'var(--text-primary, #333)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '20px' }}>🤖</span>
          <span style={{ fontSize: '15px', fontWeight: 700 }}>AI 深度分析报告</span>
          <span style={{
            padding: '2px 8px', borderRadius: '10px', fontSize: '11px',
            background: '#1a73e822', color: '#1a73e8', fontWeight: 600,
          }}>
            Claude AI
          </span>
        </div>
        <span style={{
          fontSize: '18px', transition: 'transform 0.25s',
          transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
          color: 'var(--text-secondary, #888)',
        }}>
          ▾
        </span>
      </button>

      {/* 展开内容 */}
      {expanded && (
        <div style={{
          padding: '0 20px 20px',
          borderTop: '1px solid var(--border-color, #eee)',
          fontSize: '14px', color: 'var(--text-primary, #333)',
          lineHeight: '1.7',
        }}>
          {renderMarkdown(report)}

          <p style={{
            fontSize: '11px', color: 'var(--text-secondary, #aaa)',
            marginTop: '16px', paddingTop: '12px',
            borderTop: '1px solid var(--border-color, #eee)',
          }}>
            🤖 由 Claude AI 生成 · 仅供参考，不构成投资建议 · 投资有风险，入市需谨慎
          </p>
        </div>
      )}
    </div>
  );
};

export default AIReportPanel;
