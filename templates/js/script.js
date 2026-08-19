/ ============================================================
// POS TRANSACTION WEB APP 2026
// Main JavaScript
// ============================================================

document.addEventListener("DOMContentLoaded", function () {

    // --------------------------------------------------------
    // Mobile menu
    // --------------------------------------------------------

    const menuButton = document.getElementById("menuButton");
    const sidebar = document.getElementById("sidebar");

    if (menuButton && sidebar) {
        menuButton.addEventListener("click", function () {
            sidebar.classList.toggle("active");
        });
    }


    // --------------------------------------------------------
    // Close alerts automatically
    // --------------------------------------------------------

    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {

        setTimeout(function () {

            alert.style.opacity = "0";

            setTimeout(function () {
                alert.remove();
            }, 500);

        }, 5000);

    });


    // --------------------------------------------------------
    // Show / hide password
    // --------------------------------------------------------

    const passwordToggles =
        document.querySelectorAll(".toggle-password");

    passwordToggles.forEach(function (toggle) {

        toggle.addEventListener("click", function () {

            const targetId = toggle.getAttribute("data-target");
            const input = document.getElementById(targetId);

            if (!input) {
                return;
            }

            if (input.type === "password") {

                input.type = "text";

                toggle.textContent = "Hide";

            } else {

                input.type = "password";

                toggle.textContent = "Show";
            }

        });

    });


    // --------------------------------------------------------
    // Confirm important actions
    // --------------------------------------------------------

    const confirmButtons =
        document.querySelectorAll("[data-confirm]");

    confirmButtons.forEach(function (button) {

        button.addEventListener("click", function (event) {

            const message =
                button.getAttribute("data-confirm");

            if (!confirm(message)) {
                event.preventDefault();
            }

        });

    });


    // --------------------------------------------------------
    // Amount input formatting
    // --------------------------------------------------------

    const amountInputs =
        document.querySelectorAll(
            'input[name="amount"], input.amount-input'
        );

    amountInputs.forEach(function (input) {

        input.addEventListener("input", function () {

            let value = input.value;

            // Allow numbers and decimal point only
            value = value.replace(/[^0-9.]/g, "");

            // Allow only one decimal point
            const parts = value.split(".");

            if (parts.length > 2) {
                value = parts[0] + "." + parts.slice(1).join("");
            }

            input.value = value;

        });

    });


    // --------------------------------------------------------
    // Transaction PIN
    // --------------------------------------------------------

    const pinInputs =
        document.querySelectorAll(
            'input[name="transaction_pin"], input[name="pin"]'
        );

    pinInputs.forEach(function (input) {

        input.setAttribute("maxlength", "4");
        input.setAttribute("inputmode", "numeric");

        input.addEventListener("input", function () {

            input.value =
                input.value.replace(/\D/g, "").slice(0, 4);

        });

    });


    // --------------------------------------------------------
    // Phone number input
    // --------------------------------------------------------

    const phoneInputs =
        document.querySelectorAll(
            'input[name="phone"], input[type="tel"]'
        );

    phoneInputs.forEach(function (input) {

        input.addEventListener("input", function () {

            input.value =
                input.value.replace(/[^0-9+]/g, "");

        });

    });


    // --------------------------------------------------------
    // Search transactions
    // --------------------------------------------------------

    const searchInput =
        document.getElementById("transactionSearch");

    const transactionRows =
        document.querySelectorAll(
            "#transactionsTable tbody tr"
        );

    if (searchInput && transactionRows.length > 0) {

        searchInput.addEventListener("input", function () {

            const search =
                searchInput.value.toLowerCase().trim();

            transactionRows.forEach(function (row) {

                const text =
                    row.textContent.toLowerCase();

                if (text.includes(search)) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }

            });

        });

    }


    // --------------------------------------------------------
    // Transaction type filter
    // --------------------------------------------------------

    const transactionFilter =
        document.getElementById("transactionTypeFilter");

    if (transactionFilter && transactionRows.length > 0) {

        transactionFilter.addEventListener("change", function () {

            const selected =
                transactionFilter.value.toLowerCase();

            transactionRows.forEach(function (row) {

                if (selected === "") {

                    row.style.display = "";

                    return;
                }

                const rowText =
                    row.textContent.toLowerCase();

                if (rowText.includes(selected)) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }

            });

        });

    }


    // --------------------------------------------------------
    // Calculate transaction total
    // --------------------------------------------------------

    const amountField =
        document.getElementById("amount");

    const feeField =
        document.getElementById("fee");

    const totalField =
        document.getElementById("total");

    function calculateTotal() {

        if (!amountField || !totalField) {
            return;
        }

        const amount =
            parseFloat(amountField.value) || 0;

        const fee =
            feeField
                ? parseFloat(feeField.value) || 0
                : 0;

        const total = amount + fee;

        totalField.value =
            total.toFixed(2);

    }

    if (amountField) {
        amountField.addEventListener(
            "input",
            calculateTotal
        );
    }

    if (feeField) {
        feeField.addEventListener(
            "input",
            calculateTotal
        );
    }


    // --------------------------------------------------------
    // Prevent double submission
    // --------------------------------------------------------

    const forms =
        document.querySelectorAll("form");

    forms.forEach(function (form) {

        form.addEventListener("submit", function () {

            const submitButton =
                form.querySelector(
                    'button[type="submit"], input[type="submit"]'
                );

            if (!submitButton) {
                return;
            }

            // Don't disable if already disabled
            if (submitButton.disabled) {
                return;
            }

            submitButton.disabled = true;

            if (submitButton.tagName === "BUTTON") {

                const originalText =
                    submitButton.textContent;

                submitButton.setAttribute(
                    "data-original-text",
                    originalText
                );

                submitButton.textContent =
                    "Processing...";

            }

        });

    });


    // --------------------------------------------------------
    // Logout confirmation
    // --------------------------------------------------------

    const logoutLinks =
        document.querySelectorAll(
            'a[href*="/logout"]'
        );

    logoutLinks.forEach(function (link) {

        link.addEventListener("click", function (event) {

            const confirmed =
                confirm("Are you sure you want to logout?");

            if (!confirmed) {
                event.preventDefault();
            }

        });

    });


    // --------------------------------------------------------
    // Copy transaction reference
    // --------------------------------------------------------

    const copyButtons =
        document.querySelectorAll(".copy-reference");

    copyButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            const reference =
                button.getAttribute("data-reference");

            if (!reference) {
                return;
            }

            navigator.clipboard.writeText(reference)
                .then(function () {

                    const oldText =
                        button.textContent;

                    button.textContent =
                        "Copied!";

                    setTimeout(function () {
                        button.textContent = oldText;
                    }, 1500);

                })
                .catch(function () {

                    alert(
                        "Unable to copy transaction reference."
                    );

                });

        });

    });


    // --------------------------------------------------------
    // Print receipt
    // --------------------------------------------------------

    const printButtons =
        document.querySelectorAll(".print-receipt");

    printButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            window.print();

        });

    });


    // --------------------------------------------------------
    // Automatically set current year
    // --------------------------------------------------------

    const yearElements =
        document.querySelectorAll(".current-year");

    yearElements.forEach(function (element) {

        element.textContent =
            new Date().getFullYear();

    });


    // --------------------------------------------------------
    // Console message
    // --------------------------------------------------------

    console.log(
        "POS Transaction Web App JavaScript loaded successfully."
    );

});