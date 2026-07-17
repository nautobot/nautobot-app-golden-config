/**
 * Carries all the selected devices PKs in a list view over to a Job run form.
 *
 * On page load it binds every anchor tagged with the `execute-job-link` class
 * (i.e. the entries in the "Execute" dropdown) so that, when clicked, the Device
 * PKs of the currently-checked table rows are appended to the Job run URL as
 * `?device=<pk>` query parameters. As a consequence Nautobot's Job run view
 * populates the matching `MultiObjectVar(model=Device)` form field from those
 * parameters.
 *
 * Each row-select checkbox must expose its Device PK via a `data-device-pk`
 * attribute. The checkbox `value` itself is left alone (it stays the row PK used
 * by bulk edit/delete). Rows without a Device PK are skipped.
 *
 * This is how the checkbox should look like:
 * <input type="checkbox" name="pk" value="<GoldenConfig-pk>"
 *        class="form-check-input nb-form-check-input-sm mt-2"
 *        data-device-pk="<Device-pk>">
 *
 * If no rows are selected the link is left at its pristine URL so the Job form
 * simply opens unfiltered.
 *
 * Implemented in plain JavaScript: jQuery is deprecated as of Nautobot 3.0.
 */
function bindExecuteWithSelection() {
    document.querySelectorAll("a.execute-job-link").forEach(function (link) {
        // Store the base job /run URL (without query string) so repeated clicks (and
        // back-forward cache restores) rebuild from a clean URL instead of stacking params.
        const baseHref = link.getAttribute("href");
        link.addEventListener("click", function () {
            const params = new URLSearchParams();
            document.querySelectorAll('input[name="pk"]:checked').forEach(function (checkbox) {
                const devicePk = checkbox.getAttribute("data-device-pk");
                if (devicePk) {
                    params.append("device", devicePk);
                }
            });
            const query = params.toString();
            link.setAttribute("href", query ? `${baseHref}?${query}` : baseHref);
        });
    });
}

// Self-initialize once the DOM is ready (no jQuery).
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindExecuteWithSelection);
} else {
    bindExecuteWithSelection();
}
