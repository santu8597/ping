$("#dns_query_execute_btn").on("click", function () {

            let domain = $("#domain").val().trim();
            let query_type = $("#query_type").val().trim();
            let anchor = $("#anchor").val().trim();


            if (!domain || !query_type || !anchor) {
                showError("All fields are required!");
                return;
            }

            mydata = {
                "domain": domain,
                "query_type":query_type,
                "anchor":anchor
            }

            $.ajax({
                url: `/generate-dns-query/`,
                method: "POST",
                headers: {'X-CSRFToken': document.getElementById('csrf').querySelector('input').value},
                data: mydata,
                beforeSend: function() {
          // Show loader before the request starts
                Swal.fire({
                    title: 'Processing...',
                    text: 'Please wait while we process.',
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
                            text: 'DNS Query Executed successfully.',
                            icon: 'success',
                            confirmButtonText: 'OK'
                        }).then(() => {
                           window.location.href = '/dns-command/';
                        });

                    } else {
                        showError(response.error || "Failed to add DNS query!");
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