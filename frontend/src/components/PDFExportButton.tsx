import React, { useState } from 'react';
import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';

interface PDFExportButtonProps {
  analysis: any;
}

const PDFExportButton: React.FC<PDFExportButtonProps> = ({ analysis }) => {
  const [exporting, setExporting] = useState(false);

  const exportToPDF = async () => {
    if (!analysis || exporting) return;
    setExporting(true);

    // 创建临时 div 并先挂载到 body（html2canvas 需要元素在 DOM 中）
    const tempDiv = document.createElement('div');
    tempDiv.style.cssText = [
      'position: fixed',
      'left: -9999px',
      'top: 0',
      'width: 700px',
      'padding: 30px',
      'font-family: Arial, sans-serif',
      'background: #fff',
      'color: #333',
      'font-size: 14px',
      'line-height: 1.6',
    ].join(';');

    // 标题
    const title = document.createElement('h1');
    title.textContent = `${analysis.symbol} 股票分析报告`;
    title.style.cssText = 'text-align:center;color:#2c3e50;margin-bottom:4px;font-size:22px;';
    tempDiv.appendChild(title);

    // 时间 + 数据来源
    const meta = document.createElement('p');
    meta.textContent = `生成时间：${new Date().toLocaleString()}　数据来源：${analysis.data?.data_source ?? ''}`;
    meta.style.cssText = 'text-align:center;color:#7f8c8d;margin-bottom:24px;font-size:12px;';
    tempDiv.appendChild(meta);

    // 分析结果卡片
    const resultBox = document.createElement('div');
    resultBox.style.cssText = 'background:#f8f9fa;padding:16px 20px;border-radius:6px;margin-bottom:20px;border-left:4px solid #4caf50;';
    const signalColor = analysis.signal?.includes('买入') ? '#ef5350' : analysis.signal?.includes('卖出') ? '#26a69a' : '#ff9800';
    resultBox.innerHTML = `
      <h2 style="margin:0 0 12px;font-size:16px;color:#333;">分析结果</h2>
      <table style="width:100%;border-collapse:collapse;">
        <tr><td style="padding:4px 0;color:#555;width:120px;"><strong>股票代码</strong></td><td>${analysis.symbol}</td></tr>
        <tr><td style="padding:4px 0;color:#555;"><strong>最新价格</strong></td><td>${analysis.data.latest.price.toFixed(2)} 元</td></tr>
        <tr><td style="padding:4px 0;color:#555;"><strong>涨跌幅</strong></td><td>${analysis.data.latest.change_pct >= 0 ? '+' : ''}${analysis.data.latest.change_pct.toFixed(2)}%</td></tr>
        <tr><td style="padding:4px 0;color:#555;"><strong>技术评分</strong></td><td>${analysis.score > 0 ? '+' : ''}${analysis.score}</td></tr>
        <tr><td style="padding:4px 0;color:#555;"><strong>操作建议</strong></td><td><span style="color:${signalColor};font-weight:bold;">${analysis.signal}</span></td></tr>
      </table>
    `;
    tempDiv.appendChild(resultBox);

    // 分析依据
    const reasonsSection = document.createElement('div');
    reasonsSection.innerHTML = `
      <h2 style="font-size:16px;color:#333;margin-bottom:12px;">📋 分析依据</h2>
      <ul style="margin:0;padding-left:20px;">
        ${analysis.reasons.map((r: string) => `<li style="margin-bottom:6px;">${r}</li>`).join('')}
      </ul>
    `;
    tempDiv.appendChild(reasonsSection);

    // 免责声明
    const disclaimer = document.createElement('p');
    disclaimer.textContent = '风险提示：本报告仅供参考，不构成投资建议。投资者应自行评估风险，独立做出投资决策。';
    disclaimer.style.cssText = 'margin-top:24px;font-size:11px;color:#999;border-top:1px solid #eee;padding-top:12px;';
    tempDiv.appendChild(disclaimer);

    // 挂载到 body（html2canvas 必须在 DOM 中渲染）
    document.body.appendChild(tempDiv);

    try {
      const canvas = await html2canvas(tempDiv, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#ffffff',
      });

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = pageWidth - 20;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;

      // 如果内容超过一页，自动分页
      let yOffset = 10;
      let remaining = imgHeight;
      let srcY = 0;
      while (remaining > 0) {
        const pageImgHeight = Math.min(remaining, pageHeight - 20);
        pdf.addImage(imgData, 'PNG', 10, yOffset, imgWidth, pageImgHeight, undefined, 'FAST', 0);
        remaining -= pageImgHeight;
        srcY += pageImgHeight;
        if (remaining > 0) {
          pdf.addPage();
          yOffset = 10;
        }
      }

      pdf.save(`${analysis.symbol}_分析报告_${new Date().toISOString().slice(0, 10)}.pdf`);
    } catch (error) {
      console.error('PDF 导出失败:', error);
      alert('PDF 导出失败，请稍后重试');
    } finally {
      // 清理：从 DOM 中移除临时元素
      document.body.removeChild(tempDiv);
      setExporting(false);
    }
  };

  return (
    <button
      onClick={exportToPDF}
      disabled={exporting}
      className="pdf-export-btn"
      title="导出分析报告为 PDF（快捷键 Ctrl+P）"
      style={{
        marginTop: '12px',
        padding: '8px 18px',
        background: exporting ? '#ccc' : '#1a73e8',
        color: '#fff',
        border: 'none',
        borderRadius: '4px',
        cursor: exporting ? 'not-allowed' : 'pointer',
        fontSize: '14px',
        transition: 'background 0.2s',
      }}
    >
      {exporting ? '⏳ 导出中...' : '📄 导出 PDF'}
    </button>
  );
};

export default PDFExportButton;
