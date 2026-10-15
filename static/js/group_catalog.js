(() => {
    const manager = document.querySelector('[data-catalog-manager]');
    if (!manager) return;

    const list = manager.querySelector('[data-catalog-list]');
    const status = manager.querySelector('[data-catalog-status]');
    const createForm = document.querySelector('[data-catalog-create]');
    const rows = () => Array.from(list.querySelectorAll('[data-catalog-id]'));
    const fieldNames = [...new Set(Array.from(list.querySelectorAll('[data-catalog-field]'), (control) => control.dataset.catalogField))];
    const snapshot = () => rows().map((row) => ({
        id: Number(row.dataset.catalogId),
        ...Object.fromEntries(Array.from(row.querySelectorAll('[data-catalog-field]'),
            (control) => [control.dataset.catalogField, control.checked])),
    }));
    let confirmed = snapshot();
    let saving = false;
    let drag = null;

    const setStatus = (text, error = false) => {
        status.textContent = text;
        status.classList.toggle('group-field-error', error);
    };
    const setControls = () => {
        manager.setAttribute('aria-busy', String(saving));
        list.querySelectorAll('input, button').forEach((control) => {
            control.disabled = saving || Boolean(drag && control !== drag.handle);
        });
        createForm.querySelector('[type="submit"]').disabled = saving || Boolean(drag);
    };
    const apply = (items) => {
        const byId = new Map(rows().map((row) => [Number(row.dataset.catalogId), row]));
        items.forEach((state) => {
            const row = byId.get(state.id);
            if (!row) return; // Items created in another session appear on the next page load.
            row.querySelectorAll('[data-catalog-field]').forEach((control) => {
                control.checked = state[control.dataset.catalogField];
            });
            list.append(row);
        });
    };
    const save = async (action, fields, focusTarget) => {
        if (saving) return;
        saving = true;
        setControls();
        setStatus(manager.dataset.savingLabel);
        let errorMessage = null;
        try {
            const body = new FormData(manager);
            body.set('action', action);
            Object.entries(fields).forEach(([key, value]) => body.set(key, value));
            const response = await fetch(manager.action, {
                method: 'POST', body, credentials: 'same-origin', redirect: 'error',
                headers: { Accept: 'application/json' },
            });
            const payload = await response.json();
            if (!response.ok) throw new Error(payload.error || manager.dataset.errorMessage);
            const items = payload[manager.dataset.responseKey];
            if (!Array.isArray(items) || !items.every((state) => (
                Number.isInteger(state.id) && fieldNames.every((field) => typeof state[field] === 'boolean')
            ))) throw new Error(manager.dataset.errorMessage);
            apply(items);
            confirmed = snapshot();
            setStatus(manager.dataset.savedLabel);
        } catch (error) {
            apply(confirmed);
            errorMessage = error instanceof TypeError || error instanceof SyntaxError
                ? manager.dataset.errorMessage : error.message;
            setStatus(manager.dataset.errorLabel, true);
        } finally {
            saving = false;
            setControls();
            if (focusTarget && document.activeElement === document.body) {
                focusTarget.focus({ preventScroll: true });
            }
        }
        if (errorMessage) {
            if (window.LSSMessageBox && typeof window.LSSMessageBox.alert === 'function') {
                await window.LSSMessageBox.alert({
                    title: manager.dataset.errorTitle, messageMarkdown: errorMessage,
                });
            } else {
                setStatus(errorMessage, true);
            }
        }
    };

    manager.addEventListener('submit', (event) => event.preventDefault());
    createForm.addEventListener('submit', (event) => {
        if (saving || drag) event.preventDefault();
    });
    manager.addEventListener('change', (event) => {
        const control = event.target.closest('[data-catalog-field]');
        if (!control) return;
        if (saving || drag) {
            apply(confirmed);
            return;
        }
        save(manager.dataset.updateAction, {
            [manager.dataset.idField]: control.closest('[data-catalog-id]').dataset.catalogId,
            field: control.dataset.catalogField, value: String(control.checked),
        }, control);
    });

    const announcePosition = () => {
        setStatus(manager.dataset.positionLabel
            .replace('{position}', String(rows().indexOf(drag.row) + 1))
            .replace('{total}', String(rows().length)));
    };
    const begin = (handle, mode) => {
        drag = { handle, row: handle.closest('[data-catalog-id]'), mode };
        handle.setAttribute('aria-pressed', 'true');
        drag.row.classList.add('is-moving');
        list.classList.add('is-moving');
        handle.focus({ preventScroll: true });
        setControls();
        announcePosition();
    };
    const finish = (commit) => {
        if (!drag) return;
        const { handle, row, frame, pointerId } = drag;
        if (frame) cancelAnimationFrame(frame);
        if (pointerId !== undefined && list.hasPointerCapture(pointerId)) {
            list.releasePointerCapture(pointerId);
        }
        drag = null;
        handle.setAttribute('aria-pressed', 'false');
        row.classList.remove('is-moving');
        list.classList.remove('is-moving');
        if (!commit) {
            apply(confirmed);
            setStatus(manager.dataset.cancelLabel);
        }
        setControls();
        handle.focus({ preventScroll: true });
        if (commit) {
            const ids = snapshot().map((state) => state.id);
            if (ids.some((id, index) => id !== confirmed[index].id)) {
                save(manager.dataset.reorderAction, { [manager.dataset.orderField]: JSON.stringify(ids) }, handle);
            } else {
                setStatus('');
            }
        }
    };
    const moveBefore = (before) => {
        if (drag.row.nextElementSibling === before) return;
        list.insertBefore(drag.row, before);
        drag.handle.focus({ preventScroll: true });
        if (drag.mode === 'keyboard') {
            drag.row.scrollIntoView({ block: 'nearest', behavior: 'instant' });
        }
        announcePosition();
    };
    const pointerPosition = () => {
        const before = rows().find((row) => row !== drag.row && (
            drag.y < row.getBoundingClientRect().top + row.getBoundingClientRect().height / 2
        ));
        moveBefore(before || null);
    };
    const pointerFrame = () => {
        if (!drag || drag.mode !== 'pointer') return;
        if (drag.moved) {
            const edge = 60;
            const scroll = drag.y < edge ? -12 : drag.y > window.innerHeight - edge ? 12 : 0;
            if (scroll) window.scrollBy({ top: scroll, behavior: 'instant' });
            pointerPosition();
        }
        drag.frame = requestAnimationFrame(pointerFrame);
    };

    list.addEventListener('pointerdown', (event) => {
        const handle = event.target.closest('[data-catalog-handle]');
        if (!handle || saving || drag || event.button !== 0 || !event.isPrimary) return;
        event.preventDefault();
        begin(handle, 'pointer');
        Object.assign(drag, { pointerId: event.pointerId, startX: event.clientX, startY: event.clientY, y: event.clientY, moved: false });
        // Capture on the list, which stays in place while its rows move.
        list.setPointerCapture(event.pointerId);
        drag.frame = requestAnimationFrame(pointerFrame);
    });
    list.addEventListener('pointermove', (event) => {
        if (!drag || drag.mode !== 'pointer' || event.pointerId !== drag.pointerId) return;
        drag.y = event.clientY;
        drag.moved ||= Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY) > 5;
    });
    list.addEventListener('pointerup', (event) => {
        if (!drag || drag.mode !== 'pointer' || event.pointerId !== drag.pointerId) return;
        drag.y = event.clientY;
        if (drag.moved) pointerPosition();
        finish(true);
    });
    list.addEventListener('pointercancel', () => finish(false));
    window.addEventListener('blur', () => {
        if (drag) finish(false);
    });
    list.addEventListener('keydown', (event) => {
        const handle = event.target.closest('[data-catalog-handle]');
        if (!handle || saving) return;
        if (event.key === 'Escape' && drag) {
            event.preventDefault();
            finish(false);
        } else if (event.key === ' ' || event.key === 'Enter') {
            event.preventDefault();
            if (!drag) begin(handle, 'keyboard');
            else if (drag.mode === 'keyboard') finish(true);
        } else if (drag && drag.mode === 'keyboard' && ['ArrowUp', 'ArrowDown'].includes(event.key)) {
            event.preventDefault();
            const allRows = rows();
            const index = allRows.indexOf(drag.row);
            if (event.key === 'ArrowUp' && index > 0) moveBefore(allRows[index - 1]);
            if (event.key === 'ArrowDown' && index < allRows.length - 1) moveBefore(allRows[index + 2] || null);
        }
    });
    setControls();
})();
