/**
 * Render read-only Monaco diff editors into content that is inserted after page load
 * (for example a modal body or an AJAX-populated tab).
 *
 * Monaco itself is loaded by Nautobot core's `js/editor.js`, which only initializes
 * `.nb-editor-container` elements present at DOMContentLoaded and exposes no hook for
 * containers added later. Pages that use this helper therefore include `js/editor.js`
 * plus a hidden `.nb-editor-container`, so that core loads Monaco with its own static
 * paths and worker setup. This helper then only relies on the standard `window.monaco`
 * global that Monaco itself defines, not on any of core's internals.
 *
 * Exposes:
 *   window.gcRenderMonacoDiff(host, original, modified, {sideBySide, lineNumbers}) -> Promise<editor|null>
 *   window.gcDisposeMonacoDiff(editor)
 */
(function (window, document) {
    "use strict";

    const MONACO_POLL_INTERVAL_MS = 50;
    const MONACO_TIMEOUT_MS = 15000;

    // Based on the options Nautobot core's js/editor.js uses for its diff editors, with line numbers shown.
    const DIFF_OPTIONS = {
        automaticLayout: true,
        readOnly: true,
        contextmenu: false,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        renderLineHighlight: "none",
        scrollbar: { verticalScrollbarSize: 8, horizontalScrollbarSize: 8, alwaysConsumeMouseWheel: false },
        renderOverviewRuler: false,
        enableSplitViewResizing: false,
        useInlineViewWhenSpaceIsLimited: false,
        hideUnchangedRegions: { enabled: true },
        // Indentation is significant in device configs, so whitespace-only changes must be shown.
        ignoreTrimWhitespace: false,
    };

    function currentTheme() {
        return document.documentElement.dataset.theme === "dark" ? "vs-dark" : "vs";
    }

    /** Resolve with `window.monaco` once Nautobot core has finished loading it. */
    function ensureMonaco() {
        return new Promise((resolve, reject) => {
            const deadline = Date.now() + MONACO_TIMEOUT_MS;
            (function check() {
                if (window.monaco?.editor) {
                    resolve(window.monaco);
                } else if (Date.now() > deadline) {
                    reject(
                        new Error("Monaco is not loaded; the page must include js/editor.js and a .nb-editor-container."),
                    );
                } else {
                    window.setTimeout(check, MONACO_POLL_INTERVAL_MS);
                }
            })();
        });
    }

    async function gcRenderMonacoDiff(host, original, modified, options = {}) {
        try {
            const monaco = await ensureMonaco();
            const editor = monaco.editor.createDiffEditor(host, {
                ...DIFF_OPTIONS,
                renderSideBySide: options.sideBySide !== false,
                lineNumbers: options.lineNumbers || "on",
                theme: currentTheme(),
            });
            editor.setModel({
                original: monaco.editor.createModel(original || "", "plaintext"),
                modified: monaco.editor.createModel(modified || "", "plaintext"),
            });
            return editor;
        } catch (error) {
            host.textContent = "Editor initialization failed";
            console.error("Monaco error:", error);
            return null;
        }
    }

    function gcDisposeMonacoDiff(editor) {
        if (!editor) {
            return;
        }
        const model = editor.getModel();
        editor.dispose();
        model?.original?.dispose();
        model?.modified?.dispose();
    }

    window.gcRenderMonacoDiff = gcRenderMonacoDiff;
    window.gcDisposeMonacoDiff = gcDisposeMonacoDiff;
})(window, document);
