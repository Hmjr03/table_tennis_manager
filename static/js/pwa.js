document.addEventListener("DOMContentLoaded", () => {
    const installButton = document.getElementById("pwa-install-button");
    const dialog = document.getElementById("pwa-install-dialog");
    const confirmButton = document.getElementById("pwa-install-confirm");
    const closeButton = document.getElementById("pwa-install-close");
    const message = document.getElementById("pwa-install-message");
    let installPrompt = null;

    const isStandalone = window.matchMedia("(display-mode: standalone)").matches
        || window.navigator.standalone === true;
    const isIOS = /iphone|ipad|ipod/i.test(window.navigator.userAgent);

    if ("serviceWorker" in navigator) {
        window.addEventListener("load", () => {
            navigator.serviceWorker.register("/service-worker.js", {scope: "/"});
        });
    }

    if (!installButton || !dialog || isStandalone) return;

    const openDialog = () => {
        dialog.hidden = false;
        document.body.classList.add("pwa-dialog-open");
        closeButton?.focus();
    };

    const closeDialog = () => {
        dialog.hidden = true;
        document.body.classList.remove("pwa-dialog-open");
        installButton.focus();
    };

    window.addEventListener("beforeinstallprompt", (event) => {
        event.preventDefault();
        installPrompt = event;
        installButton.hidden = false;
    });

    if (isIOS) installButton.hidden = false;

    installButton.addEventListener("click", async () => {
        if (installPrompt) {
            await installPrompt.prompt();
            await installPrompt.userChoice;
            installPrompt = null;
            installButton.hidden = true;
            return;
        }

        if (isIOS) {
            message.textContent = installButton.dataset.iosMessage;
            confirmButton.hidden = true;
            openDialog();
        }
    });

    confirmButton.addEventListener("click", async () => {
        if (!installPrompt) return;
        await installPrompt.prompt();
        await installPrompt.userChoice;
        installPrompt = null;
        installButton.hidden = true;
        closeDialog();
    });

    closeButton.addEventListener("click", closeDialog);
    dialog.addEventListener("click", (event) => {
        if (event.target === dialog) closeDialog();
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !dialog.hidden) closeDialog();
    });

    window.addEventListener("appinstalled", () => {
        installPrompt = null;
        installButton.hidden = true;
        dialog.hidden = true;
    });
});
