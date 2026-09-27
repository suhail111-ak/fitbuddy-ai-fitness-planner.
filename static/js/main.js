/**
 * FitBuddy AI – Interactive Frontend Controller
 */

document.addEventListener("DOMContentLoaded", () => {
    initFormHandlers();
    initExerciseCheckboxes();
});

/**
 * Handle form submission loading states
 */
function initFormHandlers() {
    const planForm = document.getElementById("fitnessPlanForm");
    const generateBtn = document.getElementById("generateBtn");

    if (planForm && generateBtn) {
        planForm.addEventListener("submit", () => {
            const btnText = generateBtn.querySelector(".btn-text");
            const btnSpinner = generateBtn.querySelector(".btn-spinner");
            if (btnText && btnSpinner) {
                btnText.classList.add("hidden");
                btnSpinner.classList.remove("hidden");
            }
            generateBtn.disabled = true;
        });
    }

    const feedbackForm = document.getElementById("feedbackForm");
    const feedbackBtn = document.getElementById("feedbackBtn");

    if (feedbackForm && feedbackBtn) {
        feedbackForm.addEventListener("submit", () => {
            const btnText = feedbackBtn.querySelector(".btn-text");
            const btnSpinner = feedbackBtn.querySelector(".btn-spinner");
            if (btnText && btnSpinner) {
                btnText.classList.add("hidden");
                btnSpinner.classList.remove("hidden");
            }
            feedbackBtn.disabled = true;
        });
    }
}

/**
 * Switch Day tabs in Workout Schedule
 */
function selectDayTab(version, index) {
    const container = document.getElementById(`container-${version}-plan`);
    if (!container) return;

    // Update tab buttons
    const tabButtons = container.querySelectorAll(".day-tab-btn");
    tabButtons.forEach((btn, i) => {
        if (i === index) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    // Update panels
    const panels = container.querySelectorAll(".day-panel");
    panels.forEach((panel, i) => {
        if (i === index) {
            panel.classList.add("active");
        } else {
            panel.classList.remove("active");
        }
    });
}

/**
 * Toggle between Updated Plan and Original Plan
 */
function switchPlanVersion(version) {
    const updatedContainer = document.getElementById("container-updated-plan");
    const originalContainer = document.getElementById("container-original-plan");
    const btnUpdated = document.getElementById("btnShowUpdated");
    const btnOriginal = document.getElementById("btnShowOriginal");

    if (version === "updated") {
        if (updatedContainer) updatedContainer.classList.remove("hidden");
        if (originalContainer) originalContainer.classList.add("hidden");
        if (btnUpdated) btnUpdated.classList.add("active");
        if (btnOriginal) btnOriginal.classList.remove("active");
    } else {
        if (updatedContainer) updatedContainer.classList.add("hidden");
        if (originalContainer) originalContainer.classList.remove("hidden");
        if (btnUpdated) btnUpdated.classList.remove("active");
        if (btnOriginal) btnOriginal.classList.add("active");
    }
}

/**
 * Interactive check-off for exercise rows
 */
function initExerciseCheckboxes() {
    const checkboxes = document.querySelectorAll(".ex-checkbox");
    checkboxes.forEach((cb) => {
        cb.addEventListener("change", function () {
            const row = this.closest(".exercise-row");
            if (row) {
                if (this.checked) {
                    row.classList.add("completed");
                } else {
                    row.classList.remove("completed");
                }
            }
        });
    });
}

/**
 * Insert suggested text into feedback textarea
 */
function applySuggestion(suggestionText) {
    const textarea = document.getElementById("feedbackInput");
    if (!textarea) return;

    if (textarea.value.trim() === "") {
        textarea.value = suggestionText;
    } else {
        textarea.value += " " + suggestionText;
    }
    textarea.focus();
}

/**
 * Live search filter for Admin / All-Plans view
 */
function filterAdminTable() {
    const input = document.getElementById("adminSearchInput");
    if (!input) return;

    const filter = input.value.toLowerCase();
    const rows = document.querySelectorAll("#plansTable tbody .plan-row");
    let visibleCount = 0;

    rows.forEach((row) => {
        const text = row.innerText.toLowerCase();
        if (text.includes(filter)) {
            row.style.display = "";
            visibleCount++;
        } else {
            row.style.display = "none";
        }
    });

    const countLabel = document.getElementById("visibleRowCount");
    if (countLabel) {
        countLabel.innerText = visibleCount;
    }
}
