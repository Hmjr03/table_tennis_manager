document.addEventListener("DOMContentLoaded", () => {
    const setEditorState = (editor, isOpen) => {
        editor.hidden = !isOpen;
        editor.classList.toggle("is-open", isOpen);

        const trigger = document.querySelector(
            `[aria-controls="${editor.id}"]`
        );
        if (trigger) {
            trigger.setAttribute("aria-expanded", String(isOpen));
        }

        if (isOpen) {
            const firstField = editor.querySelector("input, select, textarea");
            firstField?.focus({preventScroll: true});
        }
    };

    document.querySelectorAll(".event-inline-trigger").forEach((trigger) => {
        trigger.addEventListener("click", () => {
            const editor = document.getElementById(trigger.dataset.editorTarget);
            if (!editor) return;
            const shouldOpen = editor.hidden;

            document.querySelectorAll(".event-inline-editor").forEach((item) => {
                if (item !== editor) setEditorState(item, false);
            });
            setEditorState(editor, shouldOpen);
        });
    });

    document.querySelectorAll(".event-editor-cancel").forEach((button) => {
        button.addEventListener("click", () => {
            const editor = document.getElementById(button.dataset.editorTarget);
            if (editor) setEditorState(editor, false);
        });
    });
});
