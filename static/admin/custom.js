// admin/custom.js

(function () {
    console.log("Custom JS loaded!");

    // ------------------------------
    // 0️⃣ Load Bootstrap JS via CDN
    // ------------------------------
    function loadBootstrapJS() {
        const bootstrapScript = document.createElement("script");
        bootstrapScript.src = "https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js";
        document.head.appendChild(bootstrapScript);
        console.log("Bootstrap JS loaded via CDN");
    }

    // ------------------------------
    // 1️⃣ Highlight active sidebar links
    // ------------------------------
    function highlightSidebarLinks() {
        const currentUrl = window.location.href;
        const navLinks = document.querySelectorAll(".nav-link");

        navLinks.forEach(link => {
            try {
                const linkObj = new URL(link.href, window.location.origin);
                const currentObj = new URL(currentUrl, window.location.origin);

                const pathMatch = linkObj.pathname === currentObj.pathname;

                let queryMatch = true;
                linkObj.searchParams.forEach((value, key) => {
                    if (currentObj.searchParams.get(key) !== value) {
                        queryMatch = false;
                    }
                });

                if (pathMatch && queryMatch) {
                    link.classList.add("active");
                } else {
                    link.classList.remove("active");
                }
            } catch (e) {
                console.warn("Error parsing URL:", link.href, e);
            }
        });
    }

    // ------------------------------
    // 2️⃣ Get current logged-in username
    // ------------------------------
    function getCurrentUsername() {
        let username = "UnknownUser";
        const infoDiv = document.querySelector("div.info > a");
        if (infoDiv) {
            username = infoDiv.textContent.trim();
        }
        console.log("Current user:", username);
        return username;
    }

    // ------------------------------
    // 3️⃣ Process changelist table rows
    // ------------------------------
    function processChangelistRows(currentUsername) {
        const table = document.querySelector("#result_list");
        if (!table) {
            // console.warn("Cannot find changelist table");
            return;
        }

        const rows = table.querySelectorAll("tbody tr");
        console.log("Found rows:", rows.length);

        rows.forEach((row) => {
            const assignedToCell = row.querySelector(".field-assigned_to");
            const assignedByCell = row.querySelector(".field-assigned_by");
            const statusCell = row.querySelector(".field-status");

            if (!assignedToCell || !statusCell) return;

            const assignedUsername = assignedToCell.textContent.trim();
            const assignedByUsername = assignedByCell.textContent.trim();
            const statusSelect = statusCell.querySelector("select");
            const currentStatus = statusSelect ? statusSelect.value : "";

            if (!statusSelect) return;

            highlightCurrentUserTask(row, assignedUsername, currentUsername);
            blockUnauthorizedStatus(statusSelect, assignedUsername, currentUsername, currentStatus, assignedByUsername);
            filterStatusOptions(statusSelect, currentStatus);
        });
    }

    // ------------------------------
    // 4️⃣ Highlight tasks assigned to current user
    // ------------------------------
    function highlightCurrentUserTask(row, assignedUsername, currentUsername) {
        if (assignedUsername === currentUsername) {
            row.style.backgroundColor = "#e6ffe6"; // light green
            row.style.borderLeft = "4px solid #28a745"; // green left border
        }
    }

    // ------------------------------
    // 5️⃣ Block status editing for unauthorized users or completed tasks
    // ------------------------------
    function blockUnauthorizedStatus(statusSelect, assignedUsername, currentUsername, currentStatus, assignedByUsername) {
        // const role = window.LOGGED_IN_USER_ROLE;

        // if (assignedUsername !== currentUsername && currentStatus !== "REVIEW" || currentStatus === "COMPLETED" || (assignedUsername === currentUsername && currentStatus === "REVIEW")) {
        //     statusSelect.style.pointerEvents = "none"; // prevents editing
        //     statusSelect.style.opacity = "0.6"; // grayed out
        //     statusSelect.title = currentStatus === "REVIEW"
        //         ? "Completed tasks cannot be edited"
        //         : "You can only change status for tasks assigned to you";
        // }

        if ((currentStatus !== "REVIEW" && currentUsername !== assignedUsername) || (currentStatus === "REVIEW" && assignedByUsername !== currentUsername) || currentStatus === "COMPLETED") {
            statusSelect.style.pointerEvents = "none"; // prevents editing
            statusSelect.style.opacity = "0.6"; // grayed out
            statusSelect.title = currentStatus === "REVIEW"
                ? "Completed tasks cannot be edited"
                : "You can only change status for tasks assigned to you";
        }


    }

    // ------------------------------
    // 6️⃣ Filter status options to allowed two-step progression
    // ------------------------------
    function filterStatusOptions(statusSelect, currentStatus) {
        const allowedOptions = [];
        if (currentStatus === "PENDING") {
            allowedOptions.push("PENDING", "IN_PROGRESS");
        } else if (currentStatus === "IN_PROGRESS") {
            allowedOptions.push("IN_PROGRESS", "REVIEW");
        } else if (currentStatus === "REVIEW") {
            allowedOptions.push("REVIEW", "COMPLETED");
        } else if (currentStatus === "COMPLETED") {
            allowedOptions.push("COMPLETED");
        }

        Array.from(statusSelect.options).forEach(option => {
            if (!allowedOptions.includes(option.value)) option.remove();
        });
    }


function enableTabNavigation() {
    const tabLinks = document.querySelectorAll(".nav-tabs .nav-link");

    tabLinks.forEach(link => {
        link.addEventListener("click", function(event) {
            const tabId = this.getAttribute("href"); // e.g., #general-tab

            // Update the URL without reloading
            history.replaceState(null, "", tabId);

            // Activate the clicked tab
            tabLinks.forEach(l => l.classList.remove("active"));
            this.classList.add("active");

            const tabContents = document.querySelectorAll(".tab-pane");
            tabContents.forEach(c => c.classList.remove("active", "show"));
            const targetPane = document.querySelector(tabId);
            if (targetPane) targetPane.classList.add("active", "show");
        });
    });

    // On page load, check if URL has hash and open that tab
    const currentHash = window.location.hash;
    if (currentHash) {
        const targetLink = document.querySelector(`.nav-tabs a[href="${currentHash}"]`);
        if (targetLink) targetLink.click();
    }
}

    // ------------------------------
    // 7️⃣ Initialize everything
    // ------------------------------
    function init() {
        loadBootstrapJS();
        enableTabNavigation();
        highlightSidebarLinks();
        const currentUsername = getCurrentUsername();
        processChangelistRows(currentUsername);
    }

    // Run init after DOM is ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

})();