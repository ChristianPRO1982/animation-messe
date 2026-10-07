(() => {
    const i18n = (window.LSS_MESSAGE_BOX_CONFIG && window.LSS_MESSAGE_BOX_CONFIG.i18n) || {};

    document.querySelectorAll("[data-app-group-confirm]").forEach((form) => {
        if (!(form instanceof HTMLFormElement)) {
            return;
        }

        form.addEventListener("submit", async (event) => {
            if (form.dataset.appGroupConfirmed === "true") {
                return;
            }
            if (!window.LSSMessageBox || typeof window.LSSMessageBox.confirm !== "function") {
                return;
            }

            event.preventDefault();
            const result = await window.LSSMessageBox.confirm({
                title: i18n.confirmationTitle || "Confirmation",
                messageMarkdown: form.dataset.appGroupConfirm || "",
                buttons: [
                    {
                        id: "yes",
                        label: i18n.yesLabel || "Oui",
                        tone: "warning",
                    },
                    {
                        id: "no",
                        label: i18n.noLabel || "Non",
                        tone: "neutral",
                    },
                ],
            });
            if (result.buttonId === "yes") {
                form.dataset.appGroupConfirmed = "true";
                form.submit();
            }
        });
    });

    document.querySelectorAll("form[data-unsaved-guard]").forEach((form) => {
        if (window.LSSUnsavedChanges && form instanceof HTMLFormElement) {
            window.LSSUnsavedChanges.attach(form);
        }
    });

    const invitationNode = document.getElementById("app-group-invitation-notice");
    if (invitationNode && window.LSSMessageBox && typeof window.LSSMessageBox.alert === "function") {
        let invitation = null;
        try {
            invitation = JSON.parse(invitationNode.textContent || "{}");
        } catch (error) {
            invitation = null;
        }
        if (invitation && invitation.messageMarkdown) {
            window.LSSMessageBox.alert({
                title: invitation.title || "Invitation",
                messageMarkdown: invitation.messageMarkdown,
                size: "default",
            });
        }
    }
})();
