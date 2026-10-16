(() => {
    const syncConfirmation = (form) => {
        const button = form.querySelector('[data-requires-confirmation]');
        if (button) {
            button.disabled = form.dataset.submitting === 'true' || !form.elements.confirmed?.checked;
        }
    };
    document.querySelectorAll('form').forEach(syncConfirmation);
    document.addEventListener('change', (event) => {
        if (event.target instanceof HTMLInputElement && event.target.name === 'confirmed' && event.target.form) {
            syncConfirmation(event.target.form);
        }
    });
    document.addEventListener('submit', async (event) => {
        const form = event.target;
        if (!(form instanceof HTMLFormElement)) return;
        event.preventDefault();
        if (form.dataset.submitting === 'true') return;
        if (event.submitter?.matches('[data-requires-confirmation]') && !form.elements.confirmed?.checked) return;
        const data = new FormData(form);
        if (event.submitter?.name) data.set(event.submitter.name, event.submitter.value);
        form.dataset.submitting = 'true';
        form.querySelectorAll('button').forEach((button) => { button.disabled = true; });
        try {
            // CORS mode preserves Origin with no-referrer; CSRF still checks the token.
            const response = await fetch(window.location.pathname, {
                method: 'POST', mode: 'cors', credentials: 'same-origin',
                referrerPolicy: 'no-referrer', redirect: 'error', body: data,
            });
            const page = new DOMParser().parseFromString(await response.text(), 'text/html');
            const main = page.querySelector('main');
            if (!main) throw new Error('Invalid response');
            document.querySelector('main').replaceWith(main);
            main.querySelectorAll('form').forEach(syncConfirmation);
            const heading = main.querySelector('h1');
            heading.tabIndex = -1;
            heading.focus();
        } catch {
            form.querySelectorAll('button').forEach((button) => { button.disabled = false; });
            const notice = document.createElement('p');
            notice.setAttribute('role', 'alert');
            notice.textContent = 'Impossible de confirmer le résultat. Rouvrez votre lien personnel pour vérifier son état.';
            form.replaceChildren(notice);
        }
    });
    const form = document.querySelector('[data-consent-preview]');
    if (!form) return;
    const secret = window.location.hash.slice(1);
    window.history.replaceState(null, '', window.location.pathname);
    if (!secret || secret.length > 128) {
        form.querySelector('[data-link-error]').hidden = false;
        return;
    }
    form.elements.secret.value = secret;
    form.requestSubmit();
})();
