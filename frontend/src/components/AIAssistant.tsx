import React from 'react';
import type { StockAnalysisResponse } from '../utils/types';

interface AIAssistantProps {
  analysis: StockAnalysisResponse | null;
  show: boolean;
  onClose: () => void;
}

const AIAssistant: React.FC<AIAssistantProps> = ({ analysis, show, onClose }) => {
  if (!show || !analysis) return null;

  const getAdvice = () => {
    if (!analysis) return "暂无数据，请先进行股票分析";
    
    const { signal, score, reasons } = analysis;
    const latest = analysis.data?.latest || {};
    const changePct = latest.change_pct || 0;
    
    let advice = "";
    
    if (signal.includes("买入")) {
      advice = `根据技术分析，当前出现买入信号。`;
      if (score > 0) advice += ` 评分为正值(${score})，表明上涨动能较强。`;
      if (reasons.some((r: string) => r.includes("MA"))) advice += ` 均线系统呈多头排列。`;
      if (changePct > 0) advice += ` 今日已上涨${changePct.toFixed(2)}%，短期趋势向好。`;
    } else if (signal.includes("卖出")) {
      advice = `根据技术分析，当前出现卖出信号。`;
      if (score < 0) advice += ` 评分为负值(${score})，表明下跌压力较大。`;
      if (reasons.some((r: string) => r.includes("MA"))) advice += ` 均线系统呈空头排列。`;
      if (changePct < 0) advice += ` 今日已下跌${Math.abs(changePct).toFixed(2)}%，短期趋势偏弱。`;
    } else {
      advice = `当前技术指标中性，建议观望。`;
      if (Math.abs(score) < 2) advice += ` 评分接近零(${score})，市场缺乏明确方向。`;
      advice += ` 可等待更明确的技术信号出现后再操作。`;
    }
    
    // Add risk warning
    advice += ` 风险提示：技术分析仅供参考，请结合基本面和市场环境综合判断。`;
    
    return advice;
  };

  return (
    <div className="ai-assistant-backdrop" onClick={onClose}>
      <div className="ai-assistant-content" onClick={e => e.stopPropagation()}>
        <div className="ai-assistant-header">
          <h3>🤖 AI分析助手</h3>
          <button className="ai-assistant-close" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="ai-assistant-body">
          <p>{getAdvice()}</p>
        </div>
        <div className="ai-assistant-footer">
          <p className="ai-disclaimer">
            本AI助手基于技术指标提供初步分析，不构成投资建议。
          </p>
        </div>
      </div>
    </div>
  );
};

export default AIAssistant;