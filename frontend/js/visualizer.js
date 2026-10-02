// Data Visualization & Table Component Engine
const Visualizer = {
  activeCharts: {},

  renderDataTable(container, columns, rows, queryId) {
    if (!rows || rows.length === 0) {
      container.innerHTML = `<div style="padding: 24px; text-align: center; color: var(--text-muted);">No records found matching this query.</div>`;
      return;
    }

    const pageSize = 15;
    let currentPage = 1;
    const totalPages = Math.ceil(rows.length / pageSize);

    const renderPage = (page) => {
      const startIdx = (page - 1) * pageSize;
      const endIdx = Math.min(startIdx + pageSize, rows.length);
      const pageRows = rows.slice(startIdx, endIdx);

      let headerHtml = columns.map(col => `<th>${Visualizer.escapeHtml(col)}</th>`).join('');
      let rowsHtml = pageRows.map(row => {
        let cells = columns.map(col => {
          let val = row[col];
          let formattedVal = Visualizer.formatCell(val);
          return `<td>${formattedVal}</td>`;
        }).join('');
        return `<tr>${cells}</tr>`;
      }).join('');

      let paginationHtml = '';
      if (totalPages > 1) {
        paginationHtml = `
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; font-size: 0.78rem; border-top: 1px solid var(--border-color); color: var(--text-muted);">
            <div>Showing ${startIdx + 1}-${endIdx} of ${rows.length} rows</div>
            <div style="display: flex; gap: 6px;">
              <button class="btn btn-secondary" style="padding: 3px 8px; font-size: 0.75rem;" ${page === 1 ? 'disabled' : ''} onclick="Visualizer.changePage('${queryId}', ${page - 1})">
                <i class="fa-solid fa-chevron-left"></i> Prev
              </button>
              <span style="padding: 4px 8px;">Page ${page} of ${totalPages}</span>
              <button class="btn btn-secondary" style="padding: 3px 8px; font-size: 0.75rem;" ${page === totalPages ? 'disabled' : ''} onclick="Visualizer.changePage('${queryId}', ${page + 1})">
                Next <i class="fa-solid fa-chevron-right"></i>
              </button>
            </div>
          </div>
        `;
      }

      const tableHtml = `
        <div style="display: flex; justify-content: flex-end; gap: 8px; margin-bottom: 8px;">
          <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem;" onclick="Visualizer.exportCsv('${queryId}')">
            <i class="fa-solid fa-file-csv"></i> Export CSV
          </button>
          <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem;" onclick="Visualizer.exportJson('${queryId}')">
            <i class="fa-solid fa-file-code"></i> Export JSON
          </button>
        </div>
        <div class="table-wrapper">
          <table class="data-table">
            <thead><tr>${headerHtml}</tr></thead>
            <tbody>${rowsHtml}</tbody>
          </table>
        </div>
        ${paginationHtml}
      `;

      container.innerHTML = tableHtml;
    };

    // Store dataset for pagination and export
    window[`_queryData_${queryId}`] = { columns, rows, container, currentPage, totalPages, renderPage };
    renderPage(1);
  },

  changePage(queryId, newPage) {
    const dataObj = window[`_queryData_${queryId}`];
    if (dataObj && newPage >= 1 && newPage <= dataObj.totalPages) {
      dataObj.currentPage = newPage;
      dataObj.renderPage(newPage);
    }
  },

  exportCsv(queryId) {
    const dataObj = window[`_queryData_${queryId}`];
    if (!dataObj) return;

    const { columns, rows } = dataObj;
    const headerRow = columns.map(c => `"${c.replace(/"/g, '""')}"`).join(',');
    const bodyRows = rows.map(row => {
      return columns.map(col => {
        let val = row[col] === null || row[col] === undefined ? '' : String(row[col]);
        return `"${val.replace(/"/g, '""')}"`;
      }).join(',');
    }).join('\n');

    const csvContent = `${headerRow}\n${bodyRows}`;
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `query_export_${Date.now()}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  },

  exportJson(queryId) {
    const dataObj = window[`_queryData_${queryId}`];
    if (!dataObj) return;

    const jsonStr = JSON.stringify(dataObj.rows, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `query_export_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  },

  renderChart(canvasElement, chartRec, columns, rows) {
    if (!window.Chart || !canvasElement || !rows || rows.length === 0) return;

    const chartId = canvasElement.id;
    if (this.activeCharts[chartId]) {
      this.activeCharts[chartId].destroy();
    }

    const chartType = (chartRec.chart_type || 'bar').toLowerCase();
    let xCol = chartRec.x_column;
    let yCol = chartRec.y_column;

    // Validate columns
    if (!xCol || !columns.includes(xCol)) {
      xCol = columns[0];
    }
    if (!yCol || !columns.includes(yCol)) {
      yCol = columns.find(c => c !== xCol && typeof rows[0][c] === 'number') || columns[1] || columns[0];
    }

    const labels = rows.map(r => String(r[xCol] ?? 'N/A'));
    const dataValues = rows.map(r => {
      let v = r[yCol];
      return typeof v === 'number' ? v : parseFloat(v) || 0;
    });

    const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
    const textColor = isDark ? '#94a3b8' : '#475569';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.06)';

    // Modern color palettes
    const palette = [
      '#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ec4899',
      '#8b5cf6', '#3b82f6', '#14b8a6', '#f97316', '#64748b'
    ];

    let config = {
      type: chartType === 'doughnut' ? 'doughnut' : (chartType === 'line' ? 'line' : 'bar'),
      data: {
        labels: labels,
        datasets: [{
          label: Visualizer.formatLabel(yCol),
          data: dataValues,
          backgroundColor: chartType === 'doughnut' || chartType === 'pie'
            ? palette
            : (chartType === 'line' ? 'rgba(99, 102, 241, 0.2)' : 'rgba(99, 102, 241, 0.8)'),
          borderColor: chartType === 'line' ? '#6366f1' : (chartType === 'bar' ? '#818cf8' : '#1e293b'),
          borderWidth: chartType === 'line' ? 3 : 1,
          borderRadius: chartType === 'bar' ? 6 : 0,
          fill: chartType === 'line',
          tension: 0.35,
          pointBackgroundColor: '#6366f1',
          pointRadius: chartType === 'line' ? 4 : 0,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: chartType === 'doughnut' || chartType === 'pie',
            labels: { color: textColor, font: { family: 'Inter', size: 11 } }
          },
          tooltip: {
            backgroundColor: '#0f172a',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            borderWidth: 1,
            titleColor: '#fff',
            bodyColor: '#38bdf8',
            padding: 10,
            cornerRadius: 8,
          }
        },
        scales: (chartType === 'doughnut' || chartType === 'pie') ? {} : {
          x: {
            grid: { color: gridColor },
            ticks: { color: textColor, font: { family: 'Inter', size: 10 } }
          },
          y: {
            grid: { color: gridColor },
            ticks: { color: textColor, font: { family: 'Inter', size: 10 } }
          }
        }
      }
    };

    this.activeCharts[chartId] = new Chart(canvasElement, config);
  },

  formatCell(val) {
    if (val === null || val === undefined) {
      return '<span style="color: var(--text-muted); font-style: italic;">null</span>';
    }
    if (typeof val === 'number') {
      // Check if currency or integer
      if (val % 1 !== 0) {
        return `<span style="font-family: var(--font-mono);">${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>`;
      }
      return `<span style="font-family: var(--font-mono);">${val.toLocaleString()}</span>`;
    }
    return Visualizer.escapeHtml(String(val));
  },

  formatLabel(str) {
    return str.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  },

  escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
};
