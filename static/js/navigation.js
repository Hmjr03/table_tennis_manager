(() => {
    const toggle = document.querySelector(".mobile-nav-toggle");
    const navigation = document.querySelector("#primary-navigation");

    if (!toggle || !navigation) {
        return;
    }

    const setOpen = (open) => {
        toggle.setAttribute("aria-expanded", String(open));
        navigation.classList.toggle("is-open", open);
        document.body.classList.toggle("mobile-nav-open", open);
    };

    toggle.addEventListener("click", () => {
        setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });

    navigation.addEventListener("click", (event) => {
        if (event.target.closest("a, button[type='submit']")) {
            setOpen(false);
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            setOpen(false);
            toggle.focus();
        }
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth > 850) {
            setOpen(false);
        }
    });
})();
