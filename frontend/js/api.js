// API Service for DB-Chat
const API = {
  baseUrl: '',

  async getDbStatus() {
    const res = await fetch(`${this.baseUrl}/api/db/status`);
    if (!res.ok) throw new Error('Failed to fetch DB status');
    return await res.json();
  },

  async getDbSchema() {
    const res = await fetch(`${this.baseUrl}/api/db/schema`);
    if (!res.ok) throw new Error('Failed to fetch schema');
    return await res.json();
  },

  async previewTable(tableName) {
    const res = await fetch(`${this.baseUrl}/api/db/preview/${encodeURIComponent(tableName)}`);
    if (!res.ok) throw new Error('Failed to preview table');
    return await res.json();
  },

  async testDbConnection(config) {
    const res = await fetch(`${this.baseUrl}/api/db/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    return await res.json();
  },

  async connectDb(config) {
    const res = await fetch(`${this.baseUrl}/api/db/connect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Connection failed');
    return data;
  },

  async getPresets() {
    const res = await fetch(`${this.baseUrl}/api/presets`);
    if (!res.ok) return { presets: [] };
    return await res.json();
  },

  async sendChatMessage(message, conversationId = null, execute = true, allowModifications = false) {
    const res = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        execute,
        allow_modifications: allowModifications
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Chat request failed');
    }
    return await res.json();
  },

  async executeRawSql(sql, allowModifications = false) {
    const res = await fetch(`${this.baseUrl}/api/query/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sql,
        allow_modifications: allowModifications
      })
    });
    return await res.json();
  },

  async getConfig() {
    const res = await fetch(`${this.baseUrl}/api/config`);
    if (!res.ok) throw new Error('Failed to load settings');
    return await res.json();
  },

  async updateConfig(payload) {
    const res = await fetch(`${this.baseUrl}/api/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Failed to update settings');
    return await res.json();
  }
};
