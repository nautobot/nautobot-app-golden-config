// Enables panels on homepage to be collapsed and expanded
document.addEventListener("DOMContentLoaded", function() {
    // Function to toggle and save state for a specific collapsible element
    function toggleAndSaveState(elementId) {
        // Remove "toggle-" in the ID to get the localStorage key the toggle btn references
        elementId = elementId.replace("toggle-", "");
        var collapsibleDiv = document.getElementById(elementId);

        // Toggle the collapsed class
        var isCollapsed = collapsibleDiv.classList.toggle("collapsed")

        // Retrieve glyphicon
        var icon = document.getElementById("collapse-icon-" + elementId);
        // Rotate glyphicon
        icon.classList.toggle("rotated");

        // Update the state in localStorage
        var isCollapsed = collapsibleDiv.classList.contains("in");
        localStorage.setItem(elementId, isCollapsed ? "collapsed" : "expanded");
        // Set Cookie value based on isCollapsed
        if (isCollapsed) {
            document.cookie = elementId + "=True; path=/";
        } else {
            document.cookie = elementId + "=False; path=/";
        }
    }

    // Add event listener to each collapsible div
    var collapseIcons = document.querySelectorAll(".collapsable-heading");
    collapseIcons.forEach(function(icon) {
        icon.addEventListener("click", function() {
            var elementId = this.id;
            toggleAndSaveState(elementId);
        });
    });
});