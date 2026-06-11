 // JavaScript to toggle dropdowns
    document.getElementById('anchor-option').addEventListener('change', function () {
        document.getElementById('anchor-dropdown').style.display = 'block';
        document.getElementById('zone-dropdown').style.display = 'none';
         document.getElementById('add_zone_btn').style.display = 'none';
    });

    document.getElementById('zone-option').addEventListener('change', function () {
        document.getElementById('anchor-dropdown').style.display = 'none';
        document.getElementById('zone-dropdown').style.display = 'block';
        document.getElementById('add_zone_btn').style.display = 'block';
    });




 $("#execute_btn").on("click", function () {
    let domain = $("#domain").val().trim();
    let anchor = $("#anchor").val().trim();
    let zone = $("#zone").val().trim();

    // Validation logic
    if (!domain) {
        showError("Domain is required.");
        return;
    }

    if ((anchor && zone) || (!anchor && !zone)) {
        showError("Please provide either Anchor or Zone.");
        return;
    }

    mydata = {
        "domain": domain,
        "anchor": anchor,
        "zone": zone
    };

    $.ajax({
        url: `/generate-traceroute-query/`,
        method: "POST",
        headers: {'X-CSRFToken': document.getElementById('csrf').querySelector('input').value},
        data: mydata,
        beforeSend: function() {
            // Show loader before the request starts
            Swal.fire({
                title: 'Processing traceroute...',
                text: 'Please wait.....',
                onBeforeOpen: () => {
                    Swal.showLoading();
                },
                allowOutsideClick: false, // Prevent closing the loader by clicking outside
                showConfirmButton: false, // Hide the confirm button
            });
        },
        success: function (response) {
            // Close the loading alert
            Swal.close();

            if (response.status == 1) {
                Swal.fire({
                    title: 'Success!',
                    text: 'Traceroute Executed successfully.',
                    icon: 'success',
                    confirmButtonText: 'OK'
                }).then(() => {
                    window.location.href = '/traceroute-command/';
                });
            } else {
                showError(response.error || "Failed to Traceroute Execute!");
            }
        },
        error: function () {
            // Close the loading alert
            Swal.close();
            showError("Something went wrong! Please try again.");
        },
        complete: function() {
            // This can be left empty or used for any additional cleanup if needed
        }
    });
});
