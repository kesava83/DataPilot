// Chat & Natural Language Query Interface
const Chat = {
  conversationId: null,
  isProcessing: false,

  async init() {
    this.conversationId = 'conv_' + Math.random().toString(36).substring(2, 10);
    await this.refreshPresets();
  },

  async refreshPresets() {
    const grid = document.getElementById('presetGrid');
    if (!grid) return;

    try {
      const data = await API.getPresets();
      const presets = data.presets || [];
      if (presets.length === 0) return;

      grid.innerHTML = presets.map((p, idx) => `
        <div class="preset-card" onclick="Chat.selectPreset('${Visualizer.escapeHtml(p.query).replace(/'/g, "\\'")}')">
          <div class="preset-tag">${Visualizer.escapeHtml(p.title)}</div>
          <div class="preset-query">${Visualizer.escapeHtml(p.query)}</div>
        </div>
      `).join('');
    } catch (err) {
      console.warn('Could not load presets:', err);
    }
  },

  selectPreset(queryText) {
    const input = document.getElementById('chatInput');
    if (input) {
      input.value = queryText;
      this.sendMessage();
    }
  },

  async sendMessage() {
    const input = document.getElementById('chatInput');
    const sendBtn = document.getElementById('chatSendBtn');
    const query = input.value.trim();

    if (!query || this.isProcessing) return;

    this.isProcessing = true;
    input.value = '';
    input.style.height = 'auto';
    sendBtn.disabled = true;

    // Hide welcome hero if still visible
    const hero = document.getElementById('welcomeHero');
    if (hero) hero.style.display = 'none';

    // Append User Message
    this.appendUserMessage(query);

    // Append Assistant Loading Bubble
    const assistantMsgId = 'msg_' + Date.now();
    this.appendAssistantLoading(assistantMsgId);
    this.scrollToBottom();

    try {
      const response = await API.sendChatMessage(query, this.conversationId, true);
      this.renderAssistantResponse(assistantMsgId, response);
    } catch (err) {
      this.renderAssistantError(assistantMsgId, err.message);
    } finally {
      this.isProcessing = false;
      sendBtn.disabled = false;
      input.focus();
      this.scrollToBottom();
    }
  },

  appendUserMessage(text) {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = 'message message-user';
    div.innerHTML = `
      <div class="message-avatar">
        <i class="fa-solid fa-user"></i>
      </div>
      <div class="message-content">
        <div class="user-bubble">${Visualizer.escapeHtml(text)}</div>
      </div>
    `;
    container.appendChild(div);
  },

  appendAssistantLoading(msgId) {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = 'message message-assistant';
    div.id = msgId;
    div.innerHTML = `
      <div class="message-avatar">
        <i class="fa-solid fa-wand-magic-sparkles"></i>
      </div>
      <div class="message-content">
        <div style="display: flex; align-items: center; gap: 10px; color: var(--text-muted); font-size: 0.88rem; padding: 12px 0;">
          <span class="spinner"></span>
          <span>Translating question to SQL and querying database...</span>
        </div>
      </div>
    `;
    container.appendChild(div);
  },

  renderAssistantResponse(msgId, data) {
    const msgEl = document.getElementById(msgId);
    if (!msgEl) return;

    const contentEl = msgEl.querySelector('.message-content');
    if (!contentEl) return;

    if (!data.success && data.error) {
      contentEl.innerHTML = `
        <div style="background: var(--danger-bg); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: var(--radius-md); padding: 16px; color: #fca5a5;">
          <div style="font-weight: 600; margin-bottom: 6px;"><i class="fa-solid fa-triangle-exclamation"></i> Query Generation Failed</div>
          <div style="font-size: 0.85rem;">${Visualizer.escapeHtml(data.error)}</div>
        </div>
      `;
      return;
    }

    const queryId = 'q_' + Math.random().toString(36).substring(2, 9);
    const sql = data.sql || '';
    const explanation = data.explanation || '';
    const summaryInsight = data.summary_insight || '';
    const results = data.results || {};
    const chartRec = data.chart_recommendation || { chart_type: 'table' };
    const rows = results.rows || [];
    const columns = results.columns || [];

    // Check if chart is applicable
    const canChart = rows.length > 0 && chartRec.chart_type && chartRec.chart_type !== 'table';

    let html = '';

    // 1. Natural Language Insight / Takeaway Box
    if (summaryInsight) {
      html += `
        <div class="insight-box">
          <i class="fa-solid fa-lightbulb insight-icon"></i>
          <div>${Visualizer.escapeHtml(summaryInsight)}</div>
        </div>
      `;
    }

    // 2. Generated SQL Code Card
    if (sql) {
      html += `
        <div class="sql-card">
          <div class="sql-card-header">
            <span style="font-family: var(--font-mono);"><i class="fa-solid fa-database" style="color: var(--accent-secondary); margin-right: 6px;"></i>Generated SQL Query</span>
            <div class="sql-actions">
              <button class="sql-btn" onclick="Chat.copySql('${queryId}')">
                <i class="fa-solid fa-copy"></i> Copy
              </button>
              <button class="sql-btn" onclick="Settings.openSqlEditor(document.getElementById('sql_${queryId}').innerText)">
                <i class="fa-solid fa-pen-to-square"></i> Edit & Run
              </button>
            </div>
          </div>
          <pre class="sql-code" id="sql_${queryId}"><code>${Visualizer.escapeHtml(sql)}</code></pre>
          ${explanation ? `<div class="sql-explanation"><i class="fa-solid fa-circle-info" style="color: var(--accent-primary); margin-right: 6px;"></i>${Visualizer.escapeHtml(explanation)}</div>` : ''}
        </div>
      `;
    }

    // 3. Results Card (Chart & Table Views)
    if (results && results.success) {
      const execTime = results.execution_time_ms ? `${results.execution_time_ms}ms` : '';
      const rowCountStr = `${results.row_count || rows.length} rows returned`;

      html += `
        <div class="results-card">
          <div class="results-header">
            <div class="results-meta">
              <span><i class="fa-solid fa-bolt" style="color: #fbbf24;"></i> ${execTime}</span>
              <span>&bull;</span>
              <span><i class="fa-solid fa-list-check"></i> ${rowCountStr}</span>
            </div>
            ${canChart ? `
              <div class="tab-group">
                <button class="tab-btn active" id="tab_chart_btn_${queryId}" onclick="Chat.switchTab('${queryId}', 'chart')">
                  <i class="fa-solid fa-chart-column"></i> Chart
                </button>
                <button class="tab-btn" id="tab_table_btn_${queryId}" onclick="Chat.switchTab('${queryId}', 'table')">
                  <i class="fa-solid fa-table"></i> Table
                </button>
              </div>
            ` : `
              <div style="font-size: 0.75rem; color: var(--text-muted);"><i class="fa-solid fa-table"></i> Table View</div>
            `}
          </div>

          ${canChart ? `
            <div class="tab-content" id="tab_chart_${queryId}">
              <div class="chart-container">
                <canvas id="canvas_${queryId}"></canvas>
              </div>
            </div>
          ` : ''}

          <div class="tab-content" id="tab_table_${queryId}" style="${canChart ? 'display: none;' : ''}">
            <div id="table_container_${queryId}"></div>
          </div>
        </div>
      `;
    } else if (results && !results.success) {
      html += `
        <div style="background: var(--danger-bg); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: var(--radius-md); padding: 14px; color: #fca5a5; font-size: 0.85rem;">
          <i class="fa-solid fa-circle-exclamation"></i> SQL Execution Error: ${Visualizer.escapeHtml(results.error)}
        </div>
      `;
    }

    contentEl.innerHTML = html;

    // After DOM rendering, attach table data and chart
    setTimeout(() => {
      const tableContainer = document.getElementById(`table_container_${queryId}`);
      if (tableContainer && rows.length > 0) {
        Visualizer.renderDataTable(tableContainer, columns, rows, queryId);
      }

      if (canChart) {
        const canvas = document.getElementById(`canvas_${queryId}`);
        if (canvas) {
          Visualizer.renderChart(canvas, chartRec, columns, rows);
        }
      }
    }, 50);
  },

  renderAssistantError(msgId, errorMsg) {
    const msgEl = document.getElementById(msgId);
    if (!msgEl) return;
    const contentEl = msgEl.querySelector('.message-content');
    if (!contentEl) return;

    contentEl.innerHTML = `
      <div style="background: var(--danger-bg); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: var(--radius-md); padding: 14px; color: #fca5a5; font-size: 0.85rem;">
        <i class="fa-solid fa-triangle-exclamation"></i> Error: ${Visualizer.escapeHtml(errorMsg)}
      </div>
    `;
  },

  switchTab(queryId, tab) {
    const chartTab = document.getElementById(`tab_chart_${queryId}`);
    const tableTab = document.getElementById(`tab_table_${queryId}`);
    const chartBtn = document.getElementById(`tab_chart_btn_${queryId}`);
    const tableBtn = document.getElementById(`tab_table_btn_${queryId}`);

    if (tab === 'chart') {
      if (chartTab) chartTab.style.display = 'block';
      if (tableTab) tableTab.style.display = 'none';
      if (chartBtn) chartBtn.classList.add('active');
      if (tableBtn) tableBtn.classList.remove('active');
    } else {
      if (chartTab) chartTab.style.display = 'none';
      if (tableTab) tableTab.style.display = 'block';
      if (chartBtn) chartBtn.classList.remove('active');
      if (tableBtn) tableBtn.classList.add('active');
    }
  },

  copySql(queryId) {
    const el = document.getElementById(`sql_${queryId}`);
    if (el) {
      navigator.clipboard.writeText(el.innerText).then(() => {
        App.showToast('SQL query copied to clipboard!', 'success');
      });
    }
  },

  scrollToBottom() {
    const container = document.getElementById('chatMessages');
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }
};
