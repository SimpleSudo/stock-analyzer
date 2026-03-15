import React from 'react';
import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';

interface PDFExportButtonProps {
  analysis: any; // StockAnalysisResponse
}

const PDFExportButton: React.FC<PDFExportButtonProps> = ({ analysis }) => {
  const exportToPDF = async () => {
    if (!analysis) return;

    try {
      // Create a temporary div for PDF content
      const tempDiv = document.createElement('div');
      tempDiv.style.padding = '20px';
      tempDiv.style.fontFamily = 'Arial, sans-serif';
      
      // Title
      const title = document.createElement('h1');
      title.textContent = `${analysis.symbol} 股票分析报告`;
      title.style.textAlign = 'center';
      title.style.color = '#2c3e50';
      tempDiv.appendChild(title);
      
      // Date
      const date = document.createElement('p');
      date.textContent = `生成时间：${new Date().toLocaleString()}`;
      date.style.textAlign = 'center';
      date.style.color = '#7f8c8d';
      date.style.marginBottom = '20px';
      tempDiv.appendChild(date);
      
      // Analysis results
      const resultsSection = document.createElement('div');
      resultsSection.innerHTML = `
        <h2>分析结果</h2>
        <p><strong>股票代码：</strong>${analysis.symbol}</p>
        <p><strong>最新价格：</strong>${analysis.data.latest.price.toFixed(2)}</p>
        <p><strong>涨跌幅：</strong>${analysis.data.latest.change_pct >= 0 ? '+' : ''}${analysis.data.latest.change_pct.toFixed(2)}%</p>
        <p><strong>技术评分：</strong>${analysis.score} (<span style="color: ${analysis.score > 0 ? 'green' : analysis.score < 0 ? 'red' : 'gray'}">${analysis.score > 0 ? '强' : analysis.score < 0 ? '弱' : '中性'}</span>)</p>
        <p><strong>操作建议：</strong>${analysis.signal}</p>
      `;
      resultsSection.style.backgroundColor = '#f8f9fa';
      resultsSection.style.padding = '15px';
      resultsSection.style.borderRadius = '5px';
      resultsSection.style.marginBottom = '20px';
      tempDiv.appendChild(resultsSection);
      
      // Reasons
      const reasonsSection = document.createElement('div');
      reasonsSection.innerHTML = `
        <h2>分析依据</h2>
        <ul>
          ${analysis.reasons.map((reason: string) => `<li>${reason}</li>`).join('')}
        </ul>
      `;
      reasonsSection.style.marginBottom = '20px';
      tempDiv.appendChild(reasonsSection);
      
      // Convert to canvas and then to PDF
      const canvas = await html2canvas(tempDiv, {
        scale: 2,
        useCORS: true
      });
      
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pageWidth = pdf.internal.pageSize.getWidth();
      const imgWidth = pageWidth - 20; // 10mm margin each side
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      
      pdf.addImage(imgData, 'PNG', 10, 10, imgWidth, imgHeight);
      pdf.save(`${analysis.symbol}_分析报告_${new Date().toISOString().slice(0,10)}.pdf`);
    } catch (error) {
      console.error('PDF导出失败:', error);
      alert('PDF导出失败，请稍后重试');
    }
  };

  return (
    <button 
      onClick={exportToPDF}
      className="pdf-export-btn"
      title="导出分析报告为PDF"
    >
      📄 导出PDF
    </button>
  );
};

export default PDFExportButton;