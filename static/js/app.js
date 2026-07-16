(() => {
  const toggle = document.querySelector('[data-sidebar-toggle]');
  const sidebar = document.querySelector('#sidebar');
  if (toggle && sidebar) toggle.addEventListener('click', () => sidebar.classList.toggle('open'));

  document.querySelectorAll('[data-item-form]').forEach((form) => {
    const quantity = form.querySelector('input[name="quantidade"]');
    const output = form.querySelector('[data-score-output]');
    const itemContainer = form.closest('.score-item');
    const points = Number(String(form.dataset.points || '0').replace(',', '.'));
    const limit = Number(String(form.dataset.limit || '0').replace(',', '.')) || null;
    const integerOnly = quantity?.dataset.integer === 'true';
    let lastValidValue = quantity?.value || '';

    const showInlineError = (message) => {
      const feedback = form.querySelector('.form-feedback');
      if (!feedback) return;
      feedback.textContent = message;
      feedback.className = 'form-feedback error';
    };

    const normalizedQuantity = () => String(quantity?.value || '').trim().replace(',', '.');

    const quantityIsValid = () => {
      const raw = String(quantity?.value || '').trim();
      if (!raw) return false;
      if (integerOnly) return /^\d+$/.test(raw) && Number(raw) > 0;
      return /^\d+([,.]\d{1,2})?$/.test(raw) && Number(raw.replace(',', '.')) > 0;
    };

    if (integerOnly && quantity) {
      quantity.addEventListener('beforeinput', (event) => {
        if (event.data && /[^0-9]/.test(event.data)) event.preventDefault();
      });
      quantity.addEventListener('paste', (event) => {
        const pasted = event.clipboardData?.getData('text') || '';
        if (!/^\d+$/.test(pasted.trim())) {
          event.preventDefault();
          showInlineError('Este item aceita somente quantidade inteira.');
        }
      });
    }

    quantity?.addEventListener('input', () => {
      if (integerOnly && !/^\d*$/.test(quantity.value)) {
        quantity.value = lastValidValue;
        showInlineError('Este item aceita somente quantidade inteira.');
        return;
      }
      lastValidValue = quantity.value;
      const value = Number(normalizedQuantity()) || 0;
      const raw = value * points;
      const total = limit === null ? raw : Math.min(raw, limit);
      if (output) output.textContent = total.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    });

    form.addEventListener('submit', async (event) => {
      const submitter = event.submitter;
      if (!submitter || submitter.form !== form) return;
      event.preventDefault();
      const feedback = form.querySelector('.form-feedback');

      if (!quantityIsValid()) {
        showInlineError(integerOnly
          ? 'Informe uma quantidade inteira maior que zero.'
          : 'Informe uma quantidade válida, maior que zero, com até duas casas decimais.');
        quantity?.focus();
        return;
      }

      submitter.disabled = true;
      submitter.textContent = 'Salvando...';
      try {
        const response = await fetch(form.action, {
          method: 'POST', body: new FormData(form), headers: {'X-Requested-With': 'XMLHttpRequest'}
        });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.erro || 'Não foi possível salvar.');
        if (output) output.textContent = Number(data.pontuacao_item).toLocaleString('pt-BR', {minimumFractionDigits: 2});
        const total = document.querySelector('[data-request-total]');
        if (total) total.textContent = Number(data.pontuacao_total).toLocaleString('pt-BR', {minimumFractionDigits: 2});
        feedback.textContent = 'Item e comprovantes salvos com sucesso.';
        feedback.className = 'form-feedback success';
        itemContainer?.classList.add('filled');
        setTimeout(() => window.location.reload(), 500);
      } catch (error) {
        feedback.textContent = error.message;
        feedback.className = 'form-feedback error';
      } finally {
        submitter.disabled = false;
        submitter.textContent = 'Salvar item';
      }
    });
  });
})();
