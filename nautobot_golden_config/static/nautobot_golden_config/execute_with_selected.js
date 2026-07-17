/**
 * Carries all the selected devices PKs in a list view over to a Job run form.
 *
 * This gets called once on page load and it binds every anchor tagged with the 
 * `execute-job-link` class (i.e. the entries in the "Execute" dropdown) so that,
 * when clicked, the Device PKs of the currently-checked
 * table rows are appended to the Job run URL as `?device=<pk>` query parameters.
 * As a consequence nautobot's Job run view populates the matching `MultiObjectVar(model=Device)`
 * form field from those parameters.
 *
 * Each row-select checkbox must expose its Device PK via a `data-device-pk` attribute.
 * The checkbox `value` itself is left alone (it stays the row PK used by bulk edit/delete). 
 * Rows without a Device PK are skipped.
 *
 * This is how the checkbox should look like:
 * <input type="checkbox" name="pk" value="<GoldenConfig-pk>"
 *        class="form-check-input nb-form-check-input-sm mt-2"
 *        data-device-pk="<Device-pk>"
 *
 * If no rows are selected the link is left at its pristine URL so the Job form
 * simply opens unfiltered.
 */
function bindExecuteWithSelection() {
    $("a.execute-job-link").each(function () {
        var $link = $(this);
        /** we need to store the base job /run URL (w/o query strings) so that fast repeated clicks don't stack query params.
         *  This should protect against Back-forward cache (bfcache) restore as well. If the user clicks the execute-job-link, 
         *  href gets rewritten, lands on the job page, then hits Back, modern browsers may restore the list page from bfcache: the DOM is restored as it was
         * *including the already-modified href* and event handlers persist, but the *JS does not re-run*
         */
        var baseHref = $link.attr("href");
        $link.on("click", function () {
            var params = $('input[name="pk"]:checked')
                .map(function () {
                    var devicePk = this.getAttribute("data-device-pk");
                    return devicePk ? "device=" + encodeURIComponent(devicePk) : null;
                })
                // converts the jQuery object returned by .map() into a plain JavaScript array
                .get();
            $link.attr("href", params.length ? baseHref + "?" + params.join("&") : baseHref);
        });
    });
}
