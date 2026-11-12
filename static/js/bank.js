$(document).ready(function () {
    $("#account_number, #bank_name").on("input", function () {
        const accountNumber = $("#account_number").val();
        const bankCode = $("#bank_name").val();

        // Ensure account number is 10 digits
        if (bankCode && accountNumber.length === 10) {
            $.ajax({
                url: "{% url 'account_verification' %}",
                type: "POST",
                headers: {
                    "X-CSRFToken": "{{ csrf_token }}"
                },
                data: JSON.stringify({
                    account_number: accountNumber,
                    bank_code: bankCode
                }),
                contentType: "application/json",
                success: function (response) {
                    if (response.status) {
                        $("#account_name").val(response.data.account_name);
                    } else {
                        $("#account_name").val("");
                        alert(response.message || "Could not verify account.");
                    }
                },
                error: function () {
                    alert("An error occurred while verifying the account.");
                }
            });
        } else if (accountNumber.length > 10) {
            $("#account_name").val("");
            alert("Account number must be exactly 10 digits.");
        }
    });
});