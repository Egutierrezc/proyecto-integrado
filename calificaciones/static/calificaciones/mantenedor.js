document.addEventListener('DOMContentLoaded', () => {
    const dialogs = document.querySelectorAll('dialog');
    const basicForm = document.getElementById('basic-form');
    const qualificationForm = document.getElementById('qualification-form');
    const entryStatus = document.getElementById('entry-status');
    const entryModeInput = qualificationForm.querySelector('[name="entry_mode"]');
    const calculationConfirmedInput = qualificationForm.querySelector(
        '[name="calculation_confirmed"]',
    );
    const saveButton = qualificationForm.querySelector(
        '[data-save-qualification]',
    );
    const amountInputs = Array.from(
        qualificationForm.querySelectorAll('[data-amount-input]'),
    );
    const calculatedPreview = qualificationForm.querySelector(
        '[data-calculated-preview]',
    );
    const denominatorResult = qualificationForm.querySelector(
        '[data-denominator-result]',
    );
    const factorResults = qualificationForm.querySelectorAll(
        '[data-factor-result]',
    );
    let calculationIsCurrent = false;

    const updateSaveButton = () => {
        const needsCalculation =
            entryModeInput.value === 'amounts' && !calculationIsCurrent;
        amountInputs.forEach((input) => {
            input.required = entryModeInput.value === 'amounts';
        });
        saveButton.disabled = needsCalculation;
        saveButton.textContent = needsCalculation
            ? 'Calcula antes de grabar'
            : 'Grabar';
    };

    const clearCalculatedPreview = () => {
        calculatedPreview.hidden = true;
        calculatedPreview.open = false;
        denominatorResult.textContent = '—';
        factorResults.forEach((result) => {
            result.textContent = '—';
        });
    };

    const invalidateCalculation = ({ clearFactors = false } = {}) => {
        calculationIsCurrent = false;
        calculationConfirmedInput.value = '';
        clearCalculatedPreview();
        if (clearFactors) {
            qualificationForm
                .querySelectorAll('[name^="factor_"]')
                .forEach((input) => {
                    if (/^factor_(?:[89]|[12]\d|3[0-3])$/.test(input.name)) {
                        input.value = '';
                    }
                });
        }
        updateSaveButton();
    };

    const resetEntry = () => {
        basicForm.reset();
        qualificationForm.reset();
        calculationIsCurrent = false;
        qualificationForm.querySelectorAll('[aria-invalid]').forEach((input) => {
            input.removeAttribute('aria-invalid');
        });
        qualificationForm.querySelector('[data-tab="amounts"]').click();
        entryStatus.textContent = '';
    };

    updateSaveButton();
    basicForm.addEventListener('submit', (event) => {
        event.preventDefault();
    });

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
                invalidateCalculation({ clearFactors: true });
                qualificationForm.querySelector('[data-tab="amounts"]').click();
            }
            currentDialog?.close();
            nextDialog?.showModal();
        });
    });

    document.querySelectorAll('[data-close-dialog]').forEach((button) => {
        button.addEventListener('click', () => {
            resetEntry();
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
            entryModeInput.value = selectedPanel;
            updateSaveButton();
            entryStatus.textContent =
                selectedPanel === 'amounts' && !calculationIsCurrent
                    ? 'Completa todos los montos 8–33 y calcula los factores.'
                    : '';
        });
    });

    amountInputs.forEach((input) => {
        input.addEventListener('input', () => {
            input.removeAttribute('aria-invalid');
            invalidateCalculation({ clearFactors: true });
            if (entryModeInput.value === 'amounts') {
                entryStatus.textContent =
                    'Los montos cambiaron. Vuelve a calcular antes de grabar.';
            }
        });
    });

    qualificationForm
        .querySelectorAll('[name^="factor_"]')
        .forEach((input) => {
            input.addEventListener('input', () => {
                invalidateCalculation();
            });
        });

    document.querySelectorAll('[data-calculate-factors]').forEach((button) => {
        button.addEventListener('click', async () => {
            const missingAmounts = amountInputs.filter(
                (input) => input.value.trim() === '',
            );
            amountInputs.forEach((input) => {
                input.setAttribute(
                    'aria-invalid',
                    String(missingAmounts.includes(input)),
                );
            });
            if (missingAmounts.length) {
                invalidateCalculation();
                entryStatus.textContent =
                    'Completa todos los montos 8–33; escribe 0 si alguno no aplica.';
                missingAmounts[0].focus();
                return;
            }

            invalidateCalculation();
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
                factorResults.forEach((resultField) => {
                    resultField.textContent =
                        result.factors[resultField.dataset.factorResult];
                });
                denominatorResult.textContent = result.denominator;
                calculatedPreview.hidden = false;
                calculatedPreview.open = true;
                calculationIsCurrent = true;
                calculationConfirmedInput.value = 'true';
                updateSaveButton();
                entryStatus.textContent =
                    'Factores calculados. Revisa el resultado y graba cuando esté listo.';
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
        if (
            entryModeInput.value === 'amounts' &&
            !calculationIsCurrent
        ) {
            entryStatus.textContent =
                'Completa todos los montos 8–33 y calcula los factores antes de grabar.';
            return;
        }
        entryStatus.textContent = 'Guardando calificación…';
        saveButton.disabled = true;
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
            updateSaveButton();
        }
    });

    document.getElementById('search-form')?.addEventListener('reset', () => {
        window.setTimeout(() => {
            window.location.href = window.location.pathname;
        }, 0);
    });

    dialogs.forEach((dialog) => {
        dialog.addEventListener('cancel', () => {
            resetEntry();
        });
        dialog.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                event.preventDefault();
                resetEntry();
                dialog.close();
            }
        });
        dialog.addEventListener('click', (event) => {
            if (event.target === dialog) {
                resetEntry();
                dialog.close();
            }
        });
    });
});
