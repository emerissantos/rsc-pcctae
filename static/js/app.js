(() => {
  const toggle = document.querySelector('[data-sidebar-toggle]');
  const sidebar = document.querySelector('#sidebar');
  if (toggle && sidebar) toggle.addEventListener('click', () => sidebar.classList.toggle('open'));

  const csrfToken = (form) => form.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';
  const formatScore = (value) => Number(value || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});

  document.querySelectorAll('[data-item-form]').forEach((form) => {
    const quantity = form.querySelector('input[name="quantidade"]');
    const output = form.querySelector('[data-score-output]');
    const itemContainer = form.closest('.score-item');
    const saveButton = form.querySelector('[data-save-item]');
    const uploadInput = form.querySelector('[data-upload-input]');
    const uploadList = form.querySelector('[data-upload-list]');
    const points = Number(String(form.dataset.points || '0').replace(',', '.'));
    const limit = Number(String(form.dataset.limit || '0').replace(',', '.')) || null;
    const integerOnly = quantity?.dataset.integer === 'true';
    const requiresUpload = form.dataset.requiresUpload === 'true';
    const hasSavedDocument = form.dataset.hasDocument === 'true';
    const uploads = new Map();
    let uploadsInProgress = 0;
    let lastValidValue = quantity?.value || '';

    const feedback = form.querySelector('.form-feedback');
    const showFeedback = (message, type = '') => {
      if (!feedback) return;
      feedback.textContent = message;
      feedback.className = `form-feedback ${type}`.trim();
    };
    const normalizedQuantity = () => String(quantity?.value || '').trim().replace(',', '.');
    const quantityIsValid = () => {
      const raw = String(quantity?.value || '').trim();
      if (!raw) return false;
      if (integerOnly) return /^\d+$/.test(raw) && Number(raw) > 0;
      return /^\d+([,.]\d{1,2})?$/.test(raw) && Number(raw.replace(',', '.')) > 0;
    };
    const updateSaveState = () => {
      const completed = [...uploads.values()].filter((item) => item.status === 'done').length;
      const errors = [...uploads.values()].some((item) => item.status === 'error');
      const hasDocument = hasSavedDocument || completed > 0;
      saveButton.disabled = !(quantityIsValid() && uploadsInProgress === 0 && !errors && (!requiresUpload || hasDocument));
      if (uploadsInProgress > 0) showFeedback('Aguarde o término do envio dos comprovantes.');
    };
    const updateScore = () => {
      if (!quantityIsValid()) { if (output) output.textContent = '—'; updateSaveState(); return; }
      const raw = Number(normalizedQuantity()) * points;
      if (output) output.textContent = formatScore(limit === null ? raw : Math.min(raw, limit));
      updateSaveState();
    };

    if (integerOnly && quantity) {
      quantity.addEventListener('beforeinput', (event) => { if (event.data && /[^0-9]/.test(event.data)) event.preventDefault(); });
      quantity.addEventListener('paste', (event) => {
        const pasted = event.clipboardData?.getData('text') || '';
        if (!/^\d+$/.test(pasted.trim())) { event.preventDefault(); showFeedback('Este item aceita somente quantidade inteira.', 'error'); }
      });
    }
    quantity?.addEventListener('input', () => {
      if (integerOnly && !/^\d*$/.test(quantity.value)) { quantity.value = lastValidValue; showFeedback('Este item aceita somente quantidade inteira.', 'error'); }
      else { lastValidValue = quantity.value; if (feedback?.classList.contains('error')) showFeedback(''); }
      updateScore();
    });

    const renderUpload = (file, key) => {
      const row = document.createElement('div');
      row.className = 'upload-row';
      row.innerHTML = `<div class="upload-meta"><strong></strong><small data-upload-status>Preparando envio...</small></div><div class="upload-progress"><span></span></div><button type="button" class="file-remove" title="Remover" disabled>×</button>`;
      row.querySelector('strong').textContent = file.name;
      uploadList.appendChild(row);
      uploads.set(key, {status: 'uploading', row, id: null, deleteUrl: null});
      return row;
    };
    const removeTemporaryUpload = async (key) => {
      const current = uploads.get(key); if (!current) return;
      const confirmed = window.confirm(
        'Remover este arquivo? Esta ação não poderá ser desfeita e será necessário enviá-lo novamente para utilizá-lo neste item.'
      );
      if (!confirmed) return;
      if (current.deleteUrl) {
        const response = await fetch(current.deleteUrl, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken(form),
            'X-Requested-With': 'XMLHttpRequest',
          },
        });
        if (!response.ok) {
          showFeedback('Não foi possível remover o arquivo. Tente novamente.', 'error');
          return;
        }
      }
      current.row.remove();
      uploads.delete(key);
      updateSaveState();
    };
    const uploadFile = (file, key) => new Promise((resolve, reject) => {
      const row = renderUpload(file, key); const bar = row.querySelector('.upload-progress span'); const status = row.querySelector('[data-upload-status]');
      const xhr = new XMLHttpRequest(); const data = new FormData(); data.append('arquivo', file);
      xhr.open('POST', form.dataset.uploadUrl); xhr.setRequestHeader('X-CSRFToken', csrfToken(form)); xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
      xhr.upload.onprogress = (event) => { if (event.lengthComputable) { const pct = Math.round((event.loaded / event.total) * 100); bar.style.width = `${pct}%`; status.textContent = `Enviando... ${pct}%`; } };
      xhr.onload = () => { let response = {}; try { response = JSON.parse(xhr.responseText); } catch (_) {}
        if (xhr.status < 200 || xhr.status >= 300 || !response.ok) { status.textContent = response.erro || 'Falha no envio.'; row.classList.add('error'); uploads.get(key).status = 'error'; reject(new Error(status.textContent)); return; }
        const current = uploads.get(key); current.status = 'done'; current.id = response.id; current.deleteUrl = response.delete_url; bar.style.width = '100%'; status.textContent = 'Enviado com sucesso'; row.classList.add('done'); const button = row.querySelector('button'); button.disabled = false; button.onclick = () => removeTemporaryUpload(key); resolve(response);
      };
      xhr.onerror = () => { status.textContent = 'Erro de conexão durante o envio.'; row.classList.add('error'); uploads.get(key).status = 'error'; reject(new Error(status.textContent)); };
      xhr.send(data);
    });
    uploadInput?.addEventListener('change', async () => {
      const files = [...uploadInput.files]; uploadInput.value = '';
      for (const file of files) {
        const key = `${Date.now()}-${Math.random()}`; uploadsInProgress += 1; updateSaveState();
        try { await uploadFile(file, key); } catch (error) { showFeedback(error.message, 'error'); }
        finally { uploadsInProgress -= 1; updateSaveState(); }
      }
    });

    form.addEventListener('submit', async (event) => {
      const submitter = event.submitter; if (!submitter || submitter.form !== form) return; event.preventDefault();
      if (!quantityIsValid()) { showFeedback(integerOnly ? 'Informe uma quantidade inteira maior que zero.' : 'Informe uma quantidade válida, maior que zero.', 'error'); quantity?.focus(); return; }
      if (submitter.disabled || uploadsInProgress > 0) return;
      const data = new FormData(form); data.delete('documentos_selecao');
      [...uploads.values()].filter((item) => item.status === 'done').forEach((item) => data.append('upload_ids', item.id));
      submitter.disabled = true; submitter.textContent = 'Salvando...';
      try {
        const response = await fetch(form.action, {method: 'POST', body: data, headers: {'X-Requested-With': 'XMLHttpRequest'}}); const payload = await response.json();
        if (!response.ok || !payload.ok) throw new Error(payload.erro || 'Não foi possível salvar.');
        if (output) output.textContent = formatScore(payload.pontuacao_item); const total = document.querySelector('[data-request-total]'); if (total) total.textContent = formatScore(payload.pontuacao_total);
        showFeedback('Item e comprovantes salvos com sucesso.', 'success'); itemContainer?.classList.add('filled'); setTimeout(() => window.location.reload(), 650);
      } catch (error) { showFeedback(error.message, 'error'); submitter.textContent = 'Salvar item'; updateSaveState(); }
    });
    updateScore();
  });
  document.addEventListener('submit', (event) => {
    const form = event.target.closest('form[data-confirm-message]');
    if (!form) return;
    const message = form.dataset.confirmMessage || 'Confirma esta ação? Ela não poderá ser desfeita.';
    if (!window.confirm(message)) event.preventDefault();
  });

  const gridForm = document.querySelector('[data-dynamic-grid-form]');
  if (gridForm) {
    const grid = document.querySelector('#cadastro-grid');
    const filterPanel = gridForm.querySelector('[data-filter-panel]');
    let searchTimer;

    const toggleFilters = (open) => {
      if (!filterPanel) return;
      filterPanel.classList.toggle('open', open);
      gridForm.querySelector('[data-filter-toggle]')?.setAttribute('aria-expanded', String(open));
    };
    gridForm.querySelector('[data-filter-toggle]')?.addEventListener('click', () => toggleFilters(!filterPanel?.classList.contains('open')));
    gridForm.querySelector('[data-filter-close]')?.addEventListener('click', () => toggleFilters(false));

    const syncToolbarFromUrl = (target) => {
      [...gridForm.elements].forEach((field) => {
        if (!field.name || field.type === 'submit' || field.type === 'button') return;
        const values = target.searchParams.getAll(field.name);
        if (field.type === 'checkbox' || field.type === 'radio') {
          field.checked = values.includes(field.value);
        } else if (field.name === 'per_page') {
          field.value = values[0] || '25';
        } else {
          field.value = values[0] || '';
        }
      });
      const activeFilters = [...gridForm.querySelectorAll('[data-filter-panel] [name]')]
        .filter((field) => String(field.value || '').trim() !== '').length;
      const toggleButton = gridForm.querySelector('[data-filter-toggle]');
      if (toggleButton) {
        let counter = toggleButton.querySelector('.filter-count');
        if (activeFilters && !counter) {
          counter = document.createElement('span');
          counter.className = 'filter-count';
          toggleButton.append(' ', counter);
        }
        if (counter) {
          counter.textContent = String(activeFilters);
          counter.hidden = activeFilters === 0;
        }
      }
    };

    const loadGrid = async (url, {pushState = true} = {}) => {
      if (!grid) return;
      const target = new URL(url, window.location.href);
      target.searchParams.set('partial', '1');
      grid.classList.add('grid-loading');
      try {
        const response = await fetch(target, {headers: {'X-Requested-With': 'XMLHttpRequest'}});
        if (!response.ok) throw new Error('Falha ao atualizar a listagem.');
        grid.innerHTML = await response.text();
        target.searchParams.delete('partial');
        syncToolbarFromUrl(target);
        if (pushState) window.history.replaceState({}, '', target);
      } catch (error) {
        console.error(error);
      } finally {
        grid.classList.remove('grid-loading');
      }
    };

    const submitGridForm = () => {
      const data = new FormData(gridForm);
      data.delete('page');
      const params = new URLSearchParams(data);
      loadGrid(`${gridForm.dataset.gridUrl}?${params.toString()}`);
    };
    gridForm.addEventListener('submit', (event) => { event.preventDefault(); toggleFilters(false); submitGridForm(); });
    gridForm.querySelector('[data-dynamic-search]')?.addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(submitGridForm, 400); });
    gridForm.querySelectorAll('[data-auto-submit]').forEach((field) => field.addEventListener('change', submitGridForm));
    document.addEventListener('click', (event) => {
      const link = event.target.closest('[data-grid-link]');
      if (!link || !gridForm.contains(link) && !grid?.contains(link)) return;
      event.preventDefault();
      loadGrid(link.href);
    });
    gridForm.querySelector('[data-grid-reset]')?.addEventListener('click', (event) => {
      event.preventDefault();
      gridForm.reset();
      toggleFilters(false);
      loadGrid(event.currentTarget.href);
    });
  }

})();
