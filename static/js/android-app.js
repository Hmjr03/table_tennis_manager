(function () {
    "use strict";

    const platformParameter = "platform";
    const androidPlatform = "android";
    const storageKey = "etm-android-app";
    const currentUrl = new URL(window.location.href);

    if (currentUrl.searchParams.get(platformParameter) === androidPlatform) {
        window.sessionStorage.setItem(storageKey, "1");
    }

    if (window.sessionStorage.getItem(storageKey) !== "1") {
        return;
    }

    document.documentElement.classList.add("android-app");

    document.querySelectorAll("[data-external-payment]").forEach(function (element) {
        element.remove();
    });

    document.querySelectorAll("a[href]").forEach(function (link) {
        const targetUrl = new URL(link.href, window.location.href);
        if (targetUrl.origin !== window.location.origin) {
            return;
        }
        targetUrl.searchParams.set(platformParameter, androidPlatform);
        link.href = targetUrl.toString();
    });
})();
