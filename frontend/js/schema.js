// Schema Browser Component
const SchemaBrowser = {
  schemaData: null,

  async init() {
    await this.refreshSchema();
    this.bindEvents();
  },

  async refreshSchema() {
    const container = document.getElementById('schemaTablesList');
    if (!container) return;

    container.innerHTML = `
      <div style="padding: 20px; text-align: center; color: var(--text-muted);">
        <span class="spinner"></span>
        <div style="margin-top: 8px; font-size: 0.8rem;">Loading database schema...</div>
      </div>
    `;

    try {
      this.schemaData = await API.getDbSchema();
      this.renderTables(this.schemaData.tables || []);
      
      const countEl = document.getElementById('sidebarTableCount');
      if (countEl) countEl.textContent = `${this.schemaData.table_count || 0} tables`;
    } catch (err) {
      container.innerHTML = `
        <div style="padding: 16px; color: var(--danger-color); font-size: 0.8rem;">
          <i class="fa-solid fa-triangle-exclamation"></i> Error loading schema: ${err.message}
        </div>
      `;
    }
  },

  renderTables(tables) {
    const container = document.getElementById('schemaTablesList');
    if (!container) return;

    if (!tables || tables.length === 0) {
      container.innerHTML = `
        <div style="padding: 24px 12px; text-align: center; color: var(--text-muted); font-size: 0.82rem;">
          <i class="fa-solid fa-database" style="font-size: 1.6rem; margin-bottom: 8px; opacity: 0.4;"></i>
          <div>No tables detected.</div>
          <div style="margin-top: 4px; font-size: 0.75rem;">Check your connection credentials.</div>
        </div>
      `;
      return;
    }

    container.innerHTML = tables.map(table => {
      const colItems = (table.columns || []).map(col => `
        <div class="column-item">
          <div class="column-name">
            ${col.is_primary_key ? '<i class="fa-solid fa-key pk-tag" title="Primary Key"></i>' : ''}
            ${col.foreign_key ? '<i class="fa-solid fa-link fk-tag" title="Foreign Key: ' + col.foreign_key + '"></i>' : ''}
            <span>${Visualizer.escapeHtml(col.name)}</span>
          </div>
          <span class="column-type">${Visualizer.escapeHtml(col.type)}</span>
        </div>
      `).join('');

      return `
        <div class="table-card" id="table-card-${table.table_name}">
          <div class="table-card-header" onclick="SchemaBrowser.toggleTable('${table.table_name}')">
            <div class="left-info">
              <i class="fa-solid fa-table" style="color: var(--accent-secondary); font-size: 0.8rem;"></i>
              <span>${Visualizer.escapeHtml(table.table_name)}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span class="badge">${table.row_count} rows</span>
              <i class="fa-solid fa-chevron-right chevron"></i>
            </div>
          </div>
          <div class="table-columns-container">
            <div style="display: flex; flex-direction: column; gap: 3px; max-height: 200px; overflow-y: auto;">
              ${colItems}
            </div>
            <div class="table-actions">
              <button class="table-btn" onclick="SchemaBrowser.preview('${table.table_name}')">
                <i class="fa-solid fa-eye"></i> Preview
              </button>
              <button class="table-btn" onclick="SchemaBrowser.askAboutTable('${table.table_name}')">
                <i class="fa-solid fa-wand-magic-sparkles"></i> Query
              </button>
            </div>
          </div>
        </div>
      `;
    }).join('');
  },

  toggleTable(tableName) {
    const card = document.getElementById(`table-card-${tableName}`);
    if (card) {
      card.classList.toggle('expanded');
    }
  },

  filterTables(query) {
    const q = query.toLowerCase().trim();
    if (!this.schemaData || !this.schemaData.tables) return;

    if (!q) {
      this.renderTables(this.schemaData.tables);
      return;
    }

    const filtered = this.schemaData.tables.filter(t => {
      const matchName = t.table_name.toLowerCase().includes(q);
      const matchCol = (t.columns || []).some(c => c.name.toLowerCase().includes(q));
      return matchName || matchCol;
    });

    this.renderTables(filtered);
  },

  async preview(tableName) {
    const modal = document.getElementById('previewModal');
    const titleEl = document.getElementById('previewModalTitle');
    const bodyEl = document.getElementById('previewModalBody');

    if (!modal || !titleEl || !bodyEl) return;

    titleEl.innerHTML = `<i class="fa-solid fa-table"></i> Sample rows: <strong>${Visualizer.escapeHtml(tableName)}</strong>`;
    bodyEl.innerHTML = `<div style="text-align: center; padding: 30px;"><span class="spinner"></span> Loading rows...</div>`;
    modal.classList.add('active');

    try {
      const data = await API.previewTable(tableName);
      Visualizer.renderDataTable(bodyEl, data.columns, data.rows, `preview_${tableName}`);
    } catch (err) {
      bodyEl.innerHTML = `<div style="color: var(--danger-color); padding: 16px;">Error previewing table: ${err.message}</div>`;
    }
  },

  askAboutTable(tableName) {
    const promptInput = document.getElementById('chatInput');
    if (promptInput) {
      promptInput.value = `Show summary analytics and recent records for the ${tableName} table`;
      promptInput.focus();
    }
  },

  bindEvents() {
    const searchInput = document.getElementById('tableSearchInput');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.filterTables(e.target.value);
      });
    }
  }
};
