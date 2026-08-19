"use strict";

/* =========================================================
   POS TRANSACTION WEB APP
   SCRIPT.JS
   Sending & Receiving Money
   ========================================================= */


/* =========================================================
   1. PAGE INITIALIZATION
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    setupMobileMenu();
    setupPasswordToggle();
    setupAmountInputs();
    setupConfirmPassword();
    setupPinInputs();
    setupTransactionForms();
    setupSearch();
    setupAlerts();
    setupConfirmButtons();
    setupDoubleSubmitProtection();

});


/* =========================================================
   2. MOBILE NAVIGATION
   ========================================================= */

function setupMobileMenu() {

    const menuButton =
        document.getElementById("menuButton");

    const menu =
        document.getElementById("navbarMenu");

    if (!menuButton || !menu) {
        return;
    }

    menuButton.addEventListener("click", function () {

        menu.classList.toggle("show");

    });

}


/* =========================================================
   3. PASSWORD SHOW / HIDE
   ========================================================= */

function setupPasswordToggle() {

    const buttons =
        document.querySelectorAll(".toggle-password");

    buttons.forEach(function (button) {

        button.addEventListener("click", function () {

            const target =
                button.getAttribute("data-target");

            const input =
                document.getElementById(target);

            if (!input) {
                return;
            }

            if (input.type === "password") {

                input.type = "text";

                button.textContent = "Hide";

            } else {

                input.type = "password";

                button.textContent = "Show";

            }

        });

    });

}


/* =========================================================
   4. MONEY AMOUNT INPUT
   ========================================================= */

function setupAmountInputs() {

    const inputs =
        document.querySelectorAll(
            'input[name="amount"], input[data-money="true"]'
        );

    inputs.forEach(function (input) {

        input.addEventListener("input", function () {

            let value = input.value;

            value =
                value.replace(/[^0-9.]/g, "");

            const firstDot =
                value.indexOf(".");

            if (firstDot !== -1) {

                value =
                    value.substring(0, firstDot + 1) +
                    value
                        .substring(firstDot + 1)
                        .replace(/\./g, "");

            }

            const parts =
                value.split(".");

            if (parts.length === 2) {

                parts[1] =
                    parts[1].substring(0, 2);

                value =
                    parts[0] + "." + parts[1];

            }

            input.value = value;

        });

    });

}


/* =========================================================
   5. CONFIRM PASSWORD
   ========================================================= */

function setupConfirmPassword() {

    const password =
        document.getElementById("password");

    const confirmPassword =
        document.getElementById(
            "confirm_password"
        );

    if (!password || !confirmPassword) {
        return;
    }

    function checkPassword() {

        if (
            confirmPassword.value !==
            password.value
        ) {

            confirmPassword.setCustomValidity(
                "Passwords do not match."
            );

        } else {

            confirmPassword.setCustomValidity("");

        }

    }

    password.addEventListener(
        "input",
        checkPassword
    );

    confirmPassword.addEventListener(
        "input",
        checkPassword
    );

}


/* =========================================================
   6. PIN INPUT
   ========================================================= */

function setupPinInputs() {

    const pinInputs =
        document.querySelectorAll(
            'input[name="pin"], input[data-pin="true"]'
        );

    pinInputs.forEach(function (input) {

        input.setAttribute(
            "inputmode",
            "numeric"
        );

        input.setAttribute(
            "maxlength",
            "4"
        );

        input.addEventListener(
            "input",
            function () {

                input.value =
                    input.value.replace(
                        /\D/g,
                        ""
                    ).substring(0, 4);

            }
        );

    });

}


/* =========================================================
   7. TRANSACTION FORM VALIDATION
   ========================================================= */

function setupTransactionForms() {

    const forms =
        document.querySelectorAll(
            ".send-money-form, " +
            ".receive-money-form, " +
            ".deposit-form, " +
            ".withdraw-form"
        );

    forms.forEach(function (form) {

        form.addEventListener(
            "submit",
            function (event) {

                const amountInput =
                    form.querySelector(
                        'input[name="amount"]'
                    );

                if (!amountInput) {
                    return;
                }

                const amount =
                    parseFloat(
                        amountInput.value
                    );

                if (
                    Number.isNaN(amount) ||
                    amount <= 0
                ) {

                    event.preventDefault();

                    showMessage(
                        "Please enter a valid amount.",
                        "danger"
                    );

                    amountInput.focus();

                    return;
                }

                const pinInput =
                    form.querySelector(
                        'input[name="pin"]'
                    );

                if (
                    pinInput &&
                    pinInput.value !== "" &&
                    !/^\d{4}$/.test(
                        pinInput.value
                    )
                ) {

                    event.preventDefault();

                    showMessage(
                        "Your PIN must contain exactly 4 digits.",
                        "danger"
                    );

                    pinInput.focus();

                }

            }
        );

    });

}


/* =========================================================
   8. FORMAT NIGERIAN NAIRA
   ========================================================= */

function formatNaira(amount) {

    const value =
        Number(amount);

    if (!Number.isFinite(value)) {
        return "₦0.00";
    }

    return value.toLocaleString(
        "en-NG",
        {
            style: "currency",
            currency: "NGN",
            minimumFractionDigits: 2
        }
    );

}


/* =========================================================
   9. FORMAT NUMBER ONLY
   ========================================================= */

function formatMoney(amount) {

    const value =
        Number(amount);

    if (!Number.isFinite(value)) {
        return "0.00";
    }

    return value.toLocaleString(
        "en-NG",
        {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }
    );

}


/* =========================================================
   10. TRANSACTION CONFIRMATION
   ========================================================= */

function confirmTransaction(
    transactionType,
    amount
) {

    const formattedAmount =
        formatNaira(amount);

    let message =
        "Are you sure you want to continue?";

    switch (transactionType) {

        case "send":

            message =
                "Are you sure you want to send " +
                formattedAmount +
                "?";

            break;

        case "receive":

            message =
                "Confirm receiving " +
                formattedAmount +
                "?";

            break;

        case "deposit":

            message =
                "Confirm deposit of " +
                formattedAmount +
                "?";

            break;

        case "withdraw":

            message =
                "Confirm withdrawal of " +
                formattedAmount +
                "?";

            break;

    }

    return window.confirm(message);

}


/* =========================================================
   11. SHOW MESSAGE
   ========================================================= */

function showMessage(
    message,
    type = "info"
) {

    let container =
        document.getElementById(
            "messageContainer"
        );

    if (!container) {

        container =
            document.createElement("div");

        container.id =
            "messageContainer";

        container.style.position =
            "fixed";

        container.style.top =
            "80px";

        container.style.right =
            "20px";

        container.style.zIndex =
            "99999";

        container.style.maxWidth =
            "350px";

        document.body.appendChild(
            container
        );

    }

    const messageBox =
        document.createElement("div");

    messageBox.className =
        "alert alert-" + type;

    messageBox.textContent =
        message;

    container.appendChild(
        messageBox
    );

    setTimeout(function () {

        messageBox.remove();

    }, 5000);

}


/* =========================================================
   12. ALERT CLOSE BUTTON
   ========================================================= */

function setupAlerts() {

    const closeButtons =
        document.querySelectorAll(
            ".alert-close"
        );

    closeButtons.forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                const alert =
                    button.closest(
                        ".alert"
                    );

                if (alert) {
                    alert.remove();
                }

            }
        );

    });

}


/* =========================================================
   13. AUTO HIDE ALERTS
   ========================================================= */

function autoHideAlerts() {

    const alerts =
        document.querySelectorAll(
            ".alert-auto-hide"
        );

    alerts.forEach(function (alert) {

        setTimeout(function () {

            alert.style.opacity = "0";

            alert.style.transition =
                "opacity 0.5s";

            setTimeout(function () {

                alert.remove();

            }, 500);

        }, 5000);

    });

}

document.addEventListener(
    "DOMContentLoaded",
    autoHideAlerts
);


/* =========================================================
   14. TRANSACTION SEARCH
   ========================================================= */

function setupSearch() {

    const search =
        document.getElementById(
            "transactionSearch"
        );

    const table =
        document.getElementById(
            "transactionTable"
        );

    if (!search || !table) {
        return;
    }

    search.addEventListener(
        "input",
        function () {

            const searchText =
                search.value.toLowerCase();

            const rows =
                table.querySelectorAll(
                    "tbody tr"
                );

            rows.forEach(function (row) {

                const text =
                    row.textContent.toLowerCase();

                if (
                    text.includes(searchText)
                ) {

                    row.style.display = "";

                } else {

                    row.style.display =
                        "none";

                }

            });

        }
    );

}


/* =========================================================
   15. CONFIRM BUTTONS
   ========================================================= */

function setupConfirmButtons() {

    const buttons =
        document.querySelectorAll(
            "[data-confirm]"
        );

    buttons.forEach(function (button) {

        button.addEventListener(
            "click",
            function (event) {

                const message =
                    button.getAttribute(
                        "data-confirm"
                    );

                if (
                    message &&
                    !window.confirm(message)
                ) {

                    event.preventDefault();

                }

            }
        );

    });

}


/* =========================================================
   16. DOUBLE SUBMISSION PROTECTION
   ========================================================= */

function setupDoubleSubmitProtection() {

    const forms =
        document.querySelectorAll(
            ".transaction-form"
        );

    forms.forEach(function (form) {

        form.addEventListener(
            "submit",
            function () {

                const button =
                    form.querySelector(
                        'button[type="submit"]'
                    );

                if (!button) {
                    return;
                }

                button.disabled = true;

                button.dataset.oldText =
                    button.textContent;

                button.textContent =
                    "Processing...";

            }
        );

    });

}


/* =========================================================
   17. COPY TRANSACTION REFERENCE
   ========================================================= */

function copyReference(elementId) {

    const element =
        document.getElementById(
            elementId
        );

    if (!element) {
        return;
    }

    const reference =
        element.textContent.trim();

    if (
        !navigator.clipboard
    ) {

        showMessage(
            "Copy is not supported by this browser.",
            "danger"
        );

        return;

    }

    navigator.clipboard
        .writeText(reference)
        .then(function () {

            showMessage(
                "Transaction reference copied.",
                "success"
            );

        })
        .catch(function () {

            showMessage(
                "Unable to copy transaction reference.",
                "danger"
            );

        });

}


/* =========================================================
   18. PRINT RECEIPT
   ========================================================= */

function printReceipt() {

    window.print();

}


/* =========================================================
   19. UPDATE BALANCE
   ========================================================= */

function updateBalance(
    elementId,
    balance
) {

    const element =
        document.getElementById(
            elementId
        );

    if (!element) {
        return;
    }

    element.textContent =
        formatNaira(balance);

}


/* =========================================================
   20. QUICK AMOUNT
   ========================================================= */

function setAmount(amount) {

    const input =
        document.querySelector(
            'input[name="amount"]'
        );

    if (!input) {
        return;
    }

    input.value = amount;

    input.dispatchEvent(
        new Event("input", {
            bubbles: true
        })
    );

}


/* =========================================================
   21. SEND MONEY VALIDATION
   ========================================================= */

function validateSendMoney() {

    const recipient =
        document.getElementById(
            "recipient"
        );

    const amount =
        document.getElementById(
            "amount"
        );

    const pin =
        document.getElementById(
            "pin"
        );

    if (!recipient) {
        return true;
    }

    if (
        recipient.value.trim() === ""
    ) {

        showMessage(
            "Please enter the recipient.",
            "danger"
        );

        recipient.focus();

        return false;

    }

    if (!amount) {
        return false;
    }

    const amountValue =
        parseFloat(amount.value);

    if (
        Number.isNaN(amountValue) ||
        amountValue <= 0
    ) {

        showMessage(
            "Please enter a valid amount.",
            "danger"
        );

        amount.focus();

        return false;

    }

    if (pin) {

        if (!/^\d{4}$/.test(pin.value)) {

            showMessage(
                "Please enter your 4-digit PIN.",
                "danger"
            );

            pin.focus();

            return false;

        }

    }

    return true;

}


/* =========================================================
   22. RECEIVE MONEY VALIDATION
   ========================================================= */

function validateReceiveMoney() {

    const amount =
        document.getElementById(
            "amount"
        );

    if (!amount) {
        return true;
    }

    const value =
        parseFloat(amount.value);

    if (
        Number.isNaN(value) ||
        value <= 0
    ) {

        showMessage(
            "Please enter a valid amount.",
            "danger"
        );

        amount.focus();

        return false;

    }

    return true;

}


/* =========================================================
   23. TRANSACTION TYPE
   ========================================================= */

function getTransactionType(
    element
) {

    if (!element) {
        return "";
    }

    return element.getAttribute(
        "data-transaction-type"
    ) || "";

}


/* =========================================================
   24. LOGOUT CONFIRMATION
   ========================================================= */

function confirmLogout() {

    return window.confirm(
        "Are you sure you want to logout?"
    );

}


/* =========================================================
   25. REFRESH BALANCE
   ========================================================= */

function refreshPage() {

    window.location.reload();

}