// Settings and Database Connection Management
const Settings = {
  activeDbConfig: null,
  activeAiConfig: null,

  async init() {
    await this.loadConfig();
    this.bindEvents();
  },

  async loadConfig() {
    try {
      const data = await API.getConfig();
      this.activeDbConfig = data.db;
      this.activeAiConfig = data.ai;
      this.updateNavbarBadges();
      this.populateForms();
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  },

  updateNavbarBadges() {
    const dbBadge = document.getElementById('navDbStatus');
    const aiBadge = document.getElementById('navAiStatus');

    if (dbBadge && this.activeDbConfig) {
      const isSample = this.activeDbConfig.mode === 'sample';
      const dbName = isSample ? 'Sample E-Commerce (Demo)' : `Postgres: ${this.activeDbConfig.database}`;
      dbBadge.innerHTML = `
        <span class="pulse-dot"></span>
        <span>${Visualizer.escapeHtml(dbName)}</span>
      `;
    }

    if (aiBadge && this.activeAiConfig) {
      const provider = this.activeAiConfig.provider;
      let label = 'AI: Gemini';
      if (provider === 'openai') label = `AI: OpenAI (${this.activeAiConfig.openai_model})`;
      else if (provider === 'ollama') label = `AI: Ollama (${this.activeAiConfig.ollama_model})`;
      else if (provider === 'gemini') label = `AI: Gemini (${this.activeAiConfig.gemini_model})`;
      else label = 'AI: Smart Demo Mode';

      aiBadge.innerHTML = `
        <i class="fa-solid fa-brain" style="color: var(--accent-secondary); font-size: 0.8rem;"></i>
        <span>${Visualizer.escapeHtml(label)}</span>
      `;
    }
  },

  populateForms() {
    if (this.activeDbConfig) {
      document.getElementById('dbHost').value = this.activeDbConfig.host || 'localhost';
      document.getElementById('dbPort').value = this.activeDbConfig.port || 5432;
      document.getElementById('dbName').value = this.activeDbConfig.database || 'postgres';
      document.getElementById('dbUser').value = this.activeDbConfig.user || 'postgres';
      document.getElementById('dbSchema').value = this.activeDbConfig.schema_name || 'public';
      document.getElementById('dbSsl').value = this.activeDbConfig.sslmode || 'prefer';
    }

    if (this.activeAiConfig) {
      document.getElementById('aiProviderSelect').value = this.activeAiConfig.provider || 'gemini';
      document.getElementById('geminiModelSelect').value = this.activeAiConfig.gemini_model || 'gemini-2.5-flash';
      document.getElementById('openaiModelSelect').value = this.activeAiConfig.openai_model || 'gpt-4o-mini';
      document.getElementById('ollamaBaseUrl').value = this.activeAiConfig.ollama_base_url || 'http://localhost:11434';
      document.getElementById('ollamaModel').value = this.activeAiConfig.ollama_model || 'llama3:latest';

      if (this.activeAiConfig.gemini_api_key_masked) {
        document.getElementById('geminiApiKey').placeholder = `Configured (${this.activeAiConfig.gemini_api_key_masked})`;
      }
      if (this.activeAiConfig.openai_api_key_masked) {
        document.getElementById('openaiApiKey').placeholder = `Configured (${this.activeAiConfig.openai_api_key_masked})`;
      }
      this.handleProviderChange();
    }
  },

  handleProviderChange() {
    const provider = document.getElementById('aiProviderSelect').value;
    document.getElementById('geminiSettingsGroup').style.display = provider === 'gemini' ? 'block' : 'none';
    document.getElementById('openaiSettingsGroup').style.display = provider === 'openai' ? 'block' : 'none';
    document.getElementById('ollamaSettingsGroup').style.display = provider === 'ollama' ? 'block' : 'none';
    document.getElementById('mockInfoGroup').style.display = provider === 'mock' ? 'block' : 'none';
  },

  openDbModal() {
    document.getElementById('dbModal').classList.add('active');
  },

  closeDbModal() {
    document.getElementById('dbModal').classList.remove('active');
    document.getElementById('dbTestResult').style.display = 'none';
  },

  openAiModal() {
    document.getElementById('aiModal').classList.add('active');
  },

  closeAiModal() {
    document.getElementById('aiModal').classList.remove('active');
  },

  getDbFormData() {
    return {
      mode: 'postgres',
      host: document.getElementById('dbHost').value.trim(),
      port: parseInt(document.getElementById('dbPort').value.trim()) || 5432,
      database: document.getElementById('dbName').value.trim(),
      user: document.getElementById('dbUser').value.trim(),
      password: document.getElementById('dbPassword').value,
      sslmode: document.getElementById('dbSsl').value,
      schema_name: document.getElementById('dbSchema').value.trim() || 'public'
    };
  },

  async testDbConnection() {
    const config = this.getDbFormData();
    const resultBox = document.getElementById('dbTestResult');
    const testBtn = document.getElementById('dbTestBtn');

    resultBox.style.display = 'block';
    resultBox.className = 'status-box';
    resultBox.innerHTML = `<span class="spinner"></span> Testing PostgreSQL connection...`;
    testBtn.disabled = true;

    try {
      const res = await API.testDbConnection(config);
      if (res.success) {
        resultBox.style.borderLeft = '4px solid var(--success-color)';
        resultBox.style.background = 'var(--success-bg)';
        resultBox.innerHTML = `
          <div style="color: var(--success-color); font-weight: 600;"><i class="fa-solid fa-circle-check"></i> Connection Successful!</div>
          <div style="font-size: 0.78rem; margin-top: 4px; color: var(--text-secondary);">
            Latency: ${res.latency_ms}ms &bull; Version: ${res.version} &bull; Tables detected: ${res.table_count}
          </div>
        `;
      } else {
        resultBox.style.borderLeft = '4px solid var(--danger-color)';
        resultBox.style.background = 'var(--danger-bg)';
        resultBox.innerHTML = `
          <div style="color: var(--danger-color); font-weight: 600;"><i class="fa-solid fa-circle-xmark"></i> Connection Failed</div>
          <div style="font-size: 0.78rem; margin-top: 4px; color: var(--text-secondary);">${Visualizer.escapeHtml(res.error || res.message)}</div>
        `;
      }
    } catch (err) {
      resultBox.style.borderLeft = '4px solid var(--danger-color)';
      resultBox.style.background = 'var(--danger-bg)';
      resultBox.innerHTML = `<div style="color: var(--danger-color);">${err.message}</div>`;
    } finally {
      testBtn.disabled = false;
    }
  },

  async saveDbConnection() {
    const config = this.getDbFormData();
    const saveBtn = document.getElementById('dbSaveBtn');
    saveBtn.disabled = true;
    saveBtn.innerHTML = `<span class="spinner"></span> Connecting...`;

    try {
      const res = await API.connectDb(config);
      App.showToast(`Connected to PostgreSQL: ${config.database}!`, 'success');
      this.closeDbModal();
      await this.loadConfig();
      await SchemaBrowser.refreshSchema();
      Chat.refreshPresets();
    } catch (err) {
      App.showToast(`Failed to connect: ${err.message}`, 'error');
    } finally {
      saveBtn.disabled = false;
      saveBtn.innerHTML = `Save & Connect`;
    }
  },

  async switchToSampleDb() {
    try {
      await API.connectDb({ mode: 'sample' });
      App.showToast('Switched to Instant Demo eCommerce Database!', 'info');
      this.closeDbModal();
      await this.loadConfig();
      await SchemaBrowser.refreshSchema();
      Chat.refreshPresets();
    } catch (err) {
      App.showToast(`Error switching DB: ${err.message}`, 'error');
    }
  },

  async saveAiSettings() {
    const provider = document.getElementById('aiProviderSelect').value;
    const payload = {
      ai_provider: provider,
      gemini_model: document.getElementById('geminiModelSelect').value,
      openai_model: document.getElementById('openaiModelSelect').value,
      ollama_base_url: document.getElementById('ollamaBaseUrl').value.trim(),
      ollama_model: document.getElementById('ollamaModel').value.trim(),
    };

    const gKey = document.getElementById('geminiApiKey').value.trim();
    if (gKey) payload.gemini_api_key = gKey;

    const oKey = document.getElementById('openaiApiKey').value.trim();
    if (oKey) payload.openai_api_key = oKey;

    try {
      await API.updateConfig(payload);
      App.showToast('AI Provider settings updated!', 'success');
      this.closeAiModal();
      await this.loadConfig();
    } catch (err) {
      App.showToast(`Failed to save settings: ${err.message}`, 'error');
    }
  },

  openSqlEditor(sql) {
    const modal = document.getElementById('sqlEditorModal');
    const textarea = document.getElementById('sqlEditorInput');
    const resultBox = document.getElementById('sqlEditorResult');
    if (!modal || !textarea) return;

    textarea.value = sql || '';
    resultBox.innerHTML = '';
    modal.classList.add('active');
  },

  closeSqlEditor() {
    document.getElementById('sqlEditorModal').classList.remove('active');
  },

  async runCustomSql() {
    const sql = document.getElementById('sqlEditorInput').value.trim();
    const resultBox = document.getElementById('sqlEditorResult');
    const runBtn = document.getElementById('runCustomSqlBtn');

    if (!sql) return;

    runBtn.disabled = true;
    runBtn.innerHTML = `<span class="spinner"></span> Running...`;
    resultBox.innerHTML = `<div style="text-align:center; padding: 20px;"><span class="spinner"></span> Executing query...</div>`;

    try {
      const res = await API.executeRawSql(sql);
      if (res.success && res.results) {
        Visualizer.renderDataTable(resultBox, res.results.columns, res.results.rows, `custom_${Date.now()}`);
      } else {
        resultBox.innerHTML = `<div style="color: var(--danger-color); padding: 14px; background: var(--danger-bg); border-radius: 6px;"><i class="fa-solid fa-circle-exclamation"></i> ${res.error || 'Execution failed.'}</div>`;
      }
    } catch (err) {
      resultBox.innerHTML = `<div style="color: var(--danger-color); padding: 14px;">${err.message}</div>`;
    } finally {
      runBtn.disabled = false;
      runBtn.innerHTML = `<i class="fa-solid fa-play"></i> Run SQL`;
    }
  },

  bindEvents() {
    document.getElementById('aiProviderSelect')?.addEventListener('change', () => this.handleProviderChange());
  }
};
