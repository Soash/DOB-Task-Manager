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
            const deadlineCell = row.querySelector(".field-deadline");

            if (!assignedToCell || !statusCell) return;

            const assignedUsername = assignedToCell.textContent.trim();
            const assignedByUsername = assignedByCell.textContent.trim();
            const statusSelect = statusCell.querySelector("select");
            const currentStatus = statusSelect ? statusSelect.value : "";

            markExpiredDeadline(deadlineCell);

            if (!statusSelect) return;

            highlightCurrentUserTask(row, assignedUsername, currentUsername);
            blockUnauthorizedStatus(statusSelect, assignedUsername, currentUsername, currentStatus, assignedByUsername);
            filterStatusOptions(statusSelect, currentStatus);
        });
    }

    function initDeadlineIndicators() {
        const deadlineCells = document.querySelectorAll("#result_list .field-deadline");
        deadlineCells.forEach(cell => markExpiredDeadline(cell));
    }

    function parseDeadlineDate(deadlineText) {
        if (!deadlineText) return null;

        const directDate = new Date(deadlineText);
        if (!Number.isNaN(directDate.getTime())) {
            return directDate;
        }

        const isoMatch = deadlineText.match(/(\d{4})-(\d{2})-(\d{2})/);
        if (isoMatch) {
            const year = Number(isoMatch[1]);
            const monthIndex = Number(isoMatch[2]) - 1;
            const day = Number(isoMatch[3]);
            return new Date(year, monthIndex, day);
        }

        const dmyMatch = deadlineText.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})/);
        if (dmyMatch) {
            const day = Number(dmyMatch[1]);
            const monthIndex = Number(dmyMatch[2]) - 1;
            const year = Number(dmyMatch[3]);
            return new Date(year, monthIndex, day);
        }

        const textMonthMatch = deadlineText.match(/^([A-Za-z]{3,9})\.?\s+(\d{1,2}),\s*(\d{4})$/);
        if (textMonthMatch) {
            const monthName = textMonthMatch[1].toLowerCase().slice(0, 3);
            const monthMap = {
                jan: 0,
                feb: 1,
                mar: 2,
                apr: 3,
                may: 4,
                jun: 5,
                jul: 6,
                aug: 7,
                sep: 8,
                oct: 9,
                nov: 10,
                dec: 11
            };

            if (monthMap[monthName] !== undefined) {
                const day = Number(textMonthMatch[2]);
                const year = Number(textMonthMatch[3]);
                return new Date(year, monthMap[monthName], day);
            }
        }

        return null;
    }

    function shouldApplyDeadlineStyling() {
        const isTaskList = window.location.pathname === "/admin/tasks/task/";
        if (!isTaskList) return false;

        const params = new URLSearchParams(window.location.search);
        const statusExact = params.get("status__exact");
        return statusExact === "PENDING" || statusExact === "IN_PROGRESS";
    }

    function markExpiredDeadline(deadlineCell) {
        if (!shouldApplyDeadlineStyling()) return;
        if (!deadlineCell) return;
        if (deadlineCell.querySelector(".deadline-overdue-icon")) return;

        const deadlineText = deadlineCell.textContent.trim();
        const deadlineDate = parseDeadlineDate(deadlineText);
        if (!deadlineDate) return;

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        deadlineDate.setHours(0, 0, 0, 0);
        if (deadlineDate >= today) return;

        const row = deadlineCell.closest("tr");
        if (row) {
            row.classList.add("deadline-overdue-row");
            row.style.backgroundColor = "#ffe6e6";
            row.style.borderLeft = "4px solid #dc3545";
        }

        const overdueIcon = document.createElement("span");
        overdueIcon.className = "deadline-overdue-icon";
        overdueIcon.textContent = "🟥";
        overdueIcon.title = "Deadline has passed";
        overdueIcon.style.marginLeft = "6px";
        overdueIcon.style.verticalAlign = "middle";

        // deadlineCell.appendChild(overdueIcon);
    }

    // ------------------------------
    // 4️⃣ Highlight tasks assigned to current user
    // ------------------------------
    function highlightCurrentUserTask(row, assignedUsername, currentUsername) {
        if (row.classList.contains("deadline-overdue-row")) return;

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

        if ((currentStatus !== "REVIEW" && currentUsername !== assignedUsername) || (currentStatus === "REVIEW" && assignedByUsername !== currentUsername) || currentStatus === "COMPLETED" || currentStatus === "BLOCKED") {
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
        } else if (currentStatus === "BLOCKED") {
            allowedOptions.push("BLOCKED");
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
        initDeadlineIndicators();
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