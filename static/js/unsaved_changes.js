/**
 * Unsaved Changes Guard
 *
 * Auto-activates on any <form data-unsaved-guard>.
 * Tracks dirty state on input/change events; clears on submit.
 * Exposes window.UnsavedChanges.isDirty for back-button and cancel-link checks.
 */
(function () {
    window.UnsavedChanges = { isDirty: false };

    var WARNING = 'You have unsaved changes. Are you sure you want to leave?';

    function markDirty() { window.UnsavedChanges.isDirty = true; }
    function clearDirty() { window.UnsavedChanges.isDirty = false; }

    function confirmLeave(callback) {
        if (window.UnsavedChanges.isDirty) {
            if (window.confirm(WARNING)) {
                clearDirty();
                callback();
            }
        } else {
            callback();
        }
    }

    // --- Attach to guarded forms ---
    document.addEventListener('DOMContentLoaded', function () {
        var forms = document.querySelectorAll('form[data-unsaved-guard]');
        forms.forEach(function (form) {
            form.addEventListener('input', markDirty);
            form.addEventListener('change', markDirty);
            form.addEventListener('submit', clearDirty);
        });

        // --- Guard cancel links inside guarded forms ---
        forms.forEach(function (form) {
            form.querySelectorAll('a[data-cancel-link]').forEach(function (link) {
                link.addEventListener('click', function (e) {
                    e.preventDefault();
                    confirmLeave(function () { window.location.href = link.href; });
                });
            });
        });

        // --- Guard history.back() cancel links inside guarded forms ---
        forms.forEach(function (form) {
            form.querySelectorAll('a[data-back-link]').forEach(function (link) {
                link.addEventListener('click', function (e) {
                    e.preventDefault();
                    confirmLeave(function () { window.history.back(); });
                });
            });
        });

        // --- Guard the global back button ---
        var backBtn = document.getElementById('globalBackBtn');
        if (backBtn) {
            backBtn.addEventListener('click', function () {
                confirmLeave(function () { window.history.back(); });
            });
        }
    });

    // --- beforeunload for browser-level protection ---
    window.addEventListener('beforeunload', function (e) {
        if (window.UnsavedChanges.isDirty) {
            e.preventDefault();
            e.returnValue = '';
        }
    });
})();
