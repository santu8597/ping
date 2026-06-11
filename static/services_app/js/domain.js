 $("#submitDomainModalBtn").on("click", function () {

            let domain = $("#new_domain").val().trim();
            let ip = $("#new_ip").val().trim();
            let page_state = $("#page_state").val().trim();

            if (!domain || !ip) {
                showError("Both fields are required!");
                return;
            }
            mydata = {
                "action_type": "add_domain",
                "domain": domain,
                "ip":ip
            }

            $.ajax({
                url: `/domain/`,
                method: "POST",
                headers: {'X-CSRFToken': document.getElementById('csrf').querySelector('input').value},
                data: mydata,
                beforeSend: function() {
                    Swal.fire({
                        title: 'New domain addition...',
                        text: 'Please wait.',
                        onBeforeOpen: () => {
                            Swal.showLoading();
                        },
                        allowOutsideClick: false, // Prevent closing the loader by clicking outside
                        showConfirmButton: false, // Hide the confirm button
                    });
                },
                success: function (response) {
                    Swal.close();
                    if (response.status == 1) {
                         Swal.fire({
                            title: 'Success!',
                            text: 'Domain added successfully.',
                            icon: 'success',
                            confirmButtonText: 'OK'
                        }).then(() => {

                            var obj_id=response.obj_id;
                            var optionValue;
                            if (page_state === 'traceroute') {
                                optionValue = obj_id;
                            } else {
                                optionValue = ip;
                            }
                            $('#domainModal input').val('');
                            $('#domainModal').modal('hide');
                            $("#domain").append(`<option value="${optionValue}">${domain}</option>`);
                            $("#domain_time_range").append(`<option value="${optionValue}">${domain}</option>`);
                        });

                    } else {
                        showError(response.message || "Failed to add domain!");
                    }
                },
                error: function () {
                    Swal.close();
                    showError("Something went wrong! Please try again.");
                },
                 complete: function() {
                // Close SweetAlert after the request completes (success or failure)

              }
            });
        });

 // Show Error Inside Modal
    function showError(message) {
        Swal.fire({
            icon: "error",
            title: "Error",
            text: message,
            confirmButtonColor: "#d33"
        });
    }


document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("new_ip");

    function cleanDomain(value) {
        try {
            // If value does not have protocol, add https:// for parsing
            let url = value;
            if (!/^https?:\/\//i.test(url)) {
                url = "https://" + url;
            }

            // Use URL API to safely extract hostname
            const parsed = new URL(url);
            return parsed.hostname; // keeps only domain (e.g. www.abc.com)
        } catch (e) {
            return value; // fallback if not a valid URL
        }
    }

    // On typing
    input.addEventListener("input", function () {
        input.value = cleanDomain(input.value);
    });

    // On paste
    input.addEventListener("paste", function (e) {
        e.preventDefault();
        const text = (e.clipboardData || window.clipboardData).getData("text");
        input.value = cleanDomain(text);
    });
});