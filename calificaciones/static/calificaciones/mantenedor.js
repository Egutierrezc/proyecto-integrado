document.addEventListener('DOMContentLoaded', () => {
    const dialogs = document.querySelectorAll('dialog');
    const basicForm = document.getElementById('basic-form');
    const qualificationForm = document.getElementById('qualification-form');
    const entryStatus = document.getElementById('entry-status');

    if (new URLSearchParams(window.location.search).get('nuevo') === '1') {
        document.getElementById('basic-dialog')?.showModal();
    }

    document.querySelectorAll('[data-open-dialog]').forEach((button) => {
        button.addEventListener('click', () => {
            const targetDialog = document.getElementById(button.dataset.openDialog);
            button.closest('dialog')?.close();
            targetDialog?.showModal();
        });
    });

    document.querySelectorAll('[data-next-dialog]').forEach((button) => {
        button.addEventListener('click', () => {
            const currentDialog = button.closest('dialog');
            const nextDialog = document.getElementById(button.dataset.nextDialog);
            if (currentDialog?.id === 'basic-dialog') {
                if (!basicForm.reportValidity()) {
                    return;
                }
                const values = new FormData(basicForm);
                for (const [name, value] of values.entries()) {
                    const target = document.getElementById(`entry-${name}`);
                    if (target && name !== 'isfut_isift') {
                        target.value = value;
                    }
                }
                document.getElementById('entry-isfut_isift').value =
                    basicForm.querySelector('[name="isfut_isift"]').checked
                        ? 'on'
                        : '';
                document.querySelector('[name="entry_mode"]').value = 'factors';
            }
            currentDialog?.close();
            nextDialog?.showModal();
        });
    });

    document.querySelectorAll('[data-close-dialog]').forEach((button) => {
        button.addEventListener('click', () => {
            button.closest('dialog')?.close();
        });
    });

    document.querySelectorAll('[data-tab]').forEach((tab) => {
        tab.addEventListener('click', () => {
            const dialog = tab.closest('dialog');
            const selectedPanel = tab.dataset.tab;

            dialog.querySelectorAll('[data-tab]').forEach((item) => {
                const isSelected = item === tab;
                item.classList.toggle('active', isSelected);
                item.setAttribute('aria-selected', String(isSelected));
            });

            dialog.querySelectorAll('[data-panel]').forEach((panel) => {
                panel.hidden = panel.dataset.panel !== selectedPanel;
            });
            qualificationForm.querySelector('[name="entry_mode"]').value =
                selectedPanel;
            entryStatus.textContent = '';
        });
    });

    document.querySelectorAll('[data-calculate-factors]').forEach((button) => {
        button.addEventListener('click', async () => {
            entryStatus.textContent = 'Calculando factores…';
            button.disabled = true;
            try {
                const response = await fetch(qualificationForm.dataset.calculateUrl, {
                    method: 'POST',
                    body: new FormData(qualificationForm),
                    headers: {
                        'X-CSRFToken': qualificationForm.querySelector(
                            '[name="csrfmiddlewaretoken"]',
                        ).value,
                    },
                });
                const result = await response.json();
                if (!response.ok) {
                    entryStatus.textContent = result.errors.join(' ');
                    return;
                }
                for (const [number, value] of Object.entries(result.factors)) {
                    qualificationForm.querySelector(
                        `[name="factor_${number}"]`,
                    ).value = value;
                }
                entryStatus.textContent =
                    'Factores calculados. Puedes revisarlos o modificarlos antes de grabar.';
            } catch (error) {
                entryStatus.textContent =
                    'No se pudo calcular. Revisa tu conexión e inténtalo nuevamente.';
                console.error('Error al calcular factores:', error);
            } finally {
                button.disabled = false;
            }
        });
    });

    qualificationForm?.addEventListener('submit', async (event) => {
        event.preventDefault();
        entryStatus.textContent = 'Guardando calificación…';
        const submitButton = qualificationForm.querySelector(
            'button[type="submit"]',
        );
        submitButton.disabled = true;
        try {
            const response = await fetch(qualificationForm.action, {
                method: 'POST',
                body: new FormData(qualificationForm),
                headers: {
                    'X-CSRFToken': qualificationForm.querySelector(
                        '[name="csrfmiddlewaretoken"]',
                    ).value,
                },
            });
            const result = await response.json();
            if (!response.ok) {
                entryStatus.textContent = result.errors.join(' ');
                return;
            }
            const pageUrl = new URL(window.location.href);
            pageUrl.searchParams.delete('nuevo');
            window.location.assign(pageUrl);
        } catch (error) {
            entryStatus.textContent =
                'No se pudo guardar. Revisa tu conexión e inténtalo nuevamente.';
            console.error('Error al guardar la calificación:', error);
        } finally {
            submitButton.disabled = false;
        }
    });

    document.getElementById('search-form')?.addEventListener('reset', () => {
        window.setTimeout(() => {
            window.location.href = window.location.pathname;
        }, 0);
    });

    dialogs.forEach((dialog) => {
        dialog.addEventListener('click', (event) => {
            if (event.target === dialog) {
                dialog.close();
            }
        });
    });
});
