document.addEventListener("DOMContentLoaded", function () {
    // Intercept anchor clicks and delay scroll to ensure layout is ready
    document.querySelectorAll('a[href^="#"]').forEach(function (link) {
        link.addEventListener("click", function (e) {
            e.preventDefault();
            var id = this.getAttribute("href").substring(1);
            var target = document.getElementById(id);
            if (target) {
                setTimeout(() => {
                    target.scrollIntoView({ behavior: "smooth" });
                }, 100); // delay ensures target is in correct position
            }
        });
    });

    // Handle scroll when page loads with a hash in the URL
    if (window.location.hash) {
        var id = window.location.hash.substring(1);
        var target = document.getElementById(id);
        if (target) {
            setTimeout(() => {
                target.scrollIntoView({ behavior: "smooth" });
            }, 100); // same delay applies here
        }
    }
});
