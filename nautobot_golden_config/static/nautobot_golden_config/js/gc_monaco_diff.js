/**
 * Render read-only Monaco diff views into content that is inserted after page load
 * (for example a modal body or an AJAX-populated tab).
 *
 * Monaco itself is loaded by Nautobot core's `js/editor.js`, which only initializes
 * `.nb-editor-container` elements present at DOMContentLoaded. Pages that use this helper
 * therefore include `js/editor.js` plus a hidden `.nb-editor-container` so that core loads
 * Monaco (with its own static paths and worker setup); this helper then reuses `window.monaco`.
 *
 * Exposes:
 *   window.gcRenderMonacoDiff(host, original, modified, {sideBySide}) -> Promise<editor|null>
 *       Side-by-side or inline diff of two full texts (Monaco diff editor).
 *   window.gcRenderMonacoUnifiedDiff(host, diffText) -> Promise<editor|null>
 *       A unified diff string shown in a standard editor with added/removed line highlighting.
 *   window.gcDisposeMonacoDiff(editor)
 */
(function (window, document) {
    "use strict";

    const COMMON_OPTIONS = {
        automaticLayout: true,
        readOnly: true,
        contextmenu: false,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        renderLineHighlight: "none",
        scrollbar: { verticalScrollbarSize: 8, horizontalScrollbarSize: 8, alwaysConsumeMouseWheel: false },
    };

    const DIFF_OPTIONS = {
        renderOverviewRuler: false,
        enableSplitViewResizing: false,
        useInlineViewWhenSpaceIsLimited: false,
        hideUnchangedRegions: { enabled: true },
    };

    function currentTheme() {
        return document.documentElement.dataset.theme === "dark" ? "vs-dark" : "vs";
    }

    async function ensureMonaco() {
        if (!window.monaco) {
            await window._monacoLoaderPromise;
        }
        if (!window.monaco) {
            throw new Error("Monaco is not loaded; the page must include js/editor.js and a .nb-editor-container.");
        }
        return window.monaco;
    }

    function initializationFailed(host, error) {
        host.textContent = "Editor initialization failed";
        console.error("Monaco error:", error);
        return null;
    }

    async function gcRenderMonacoDiff(host, original, modified, options = {}) {
        try {
            const monaco = await ensureMonaco();
            const editor = monaco.editor.createDiffEditor(host, {
                ...COMMON_OPTIONS,
                ...DIFF_OPTIONS,
                renderSideBySide: options.sideBySide !== false,
                theme: currentTheme(),
            });
            editor.setModel({
                original: monaco.editor.createModel(original, "plaintext"),
                modified: monaco.editor.createModel(modified, "plaintext"),
            });
            return editor;
        } catch (error) {
            return initializationFailed(host, error);
        }
    }

    /** Whole-line decorations for the header, hunk, added and removed lines of a unified diff. */
    function unifiedDiffDecorations(monaco, diffText) {
        const decorations = [];
        diffText.split("\n").forEach((line, index) => {
            let className = null;
            if (line.startsWith("+++") || line.startsWith("---")) {
                className = "gc-diff-line-header";
            } else if (line.startsWith("@@")) {
                className = "gc-diff-line-hunk";
            } else if (line.startsWith("+")) {
                className = "gc-diff-line-added";
            } else if (line.startsWith("-")) {
                className = "gc-diff-line-removed";
            }
            if (className) {
                const lineNumber = index + 1;
                decorations.push({
                    range: new monaco.Range(lineNumber, 1, lineNumber, 1),
                    options: { isWholeLine: true, className: className },
                });
            }
        });
        return decorations;
    }

    async function gcRenderMonacoUnifiedDiff(host, diffText) {
        try {
            const monaco = await ensureMonaco();
            const editor = monaco.editor.create(host, {
                ...COMMON_OPTIONS,
                value: diffText,
                language: "plaintext",
                theme: currentTheme(),
            });
            editor.createDecorationsCollection(unifiedDiffDecorations(monaco, diffText));
            return editor;
        } catch (error) {
            return initializationFailed(host, error);
        }
    }

    function gcDisposeMonacoDiff(editor) {
        if (!editor) {
            return;
        }
        const model = editor.getModel();
        if (model?.original) {
            model.original.dispose();
            model.modified.dispose();
        } else {
            model?.dispose();
        }
        editor.dispose();
    }

    window.gcRenderMonacoDiff = gcRenderMonacoDiff;
    window.gcRenderMonacoUnifiedDiff = gcRenderMonacoUnifiedDiff;
    window.gcDisposeMonacoDiff = gcDisposeMonacoDiff;
})(window, document);
