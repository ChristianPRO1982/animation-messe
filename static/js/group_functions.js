(() => {
    const manager = document.querySelector('[data-function-manager]');
    if (!manager) return;

    const list = manager.querySelector('[data-function-list]');
    const status = manager.querySelector('[data-function-status]');
    const createForm = document.querySelector('[data-function-create]');
    const rows = () => Array.from(list.querySelectorAll('[data-function-id]'));
    const snapshot = () => rows().map((row) => ({
        id: Number(row.dataset.functionId),
        is_active: row.querySelector('[data-function-field="is_active"]').checked,
        auto_edit_celebration: row.querySelector('[data-function-field="auto_edit_celebration"]').checked,
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
    const apply = (functions) => {
        const byId = new Map(rows().map((row) => [Number(row.dataset.functionId), row]));
        functions.forEach((state) => {
            const row = byId.get(state.id);
            if (!row) return; // A function created in another session appears on the next page load.
            row.querySelector('[data-function-field="is_active"]').checked = state.is_active;
            row.querySelector('[data-function-field="auto_edit_celebration"]').checked = state.auto_edit_celebration;
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
            if (!Array.isArray(payload.functions) || !payload.functions.every((state) => (
                Number.isInteger(state.id) && typeof state.is_active === 'boolean'
                && typeof state.auto_edit_celebration === 'boolean'
            ))) throw new Error(manager.dataset.errorMessage);
            apply(payload.functions);
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
        const control = event.target.closest('[data-function-field]');
        if (!control) return;
        if (saving || drag) {
            apply(confirmed);
            return;
        }
        save('update_function', {
            function_id: control.closest('[data-function-id]').dataset.functionId,
            field: control.dataset.functionField, value: String(control.checked),
        }, control);
    });

    const announcePosition = () => {
        setStatus(manager.dataset.positionLabel
            .replace('{position}', String(rows().indexOf(drag.row) + 1))
            .replace('{total}', String(rows().length)));
    };
    const begin = (handle, mode) => {
        drag = { handle, row: handle.closest('[data-function-id]'), mode };
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
                save('reorder_functions', { function_ids: JSON.stringify(ids) }, handle);
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
        const handle = event.target.closest('[data-function-handle]');
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
        const handle = event.target.closest('[data-function-handle]');
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
