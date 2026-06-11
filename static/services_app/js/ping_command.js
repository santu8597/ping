
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

     // JavaScript to toggle dropdowns
        document.getElementById('anchor-option-time').addEventListener('change', function () {
        document.getElementById('anchor-dropdown-time').style.display = 'block';
        document.getElementById('zone-dropdown-time').style.display = 'none';
        document.getElementById('add_zone_btn_time').style.display = 'none';
    });

        document.getElementById('zone-option-time').addEventListener('change', function () {
        document.getElementById('anchor-dropdown-time').style.display = 'none';
        document.getElementById('zone-dropdown-time').style.display = 'block';
        document.getElementById('add_zone_btn_time').style.display = 'block';
    });



        // Script to open report page
  window.addEventListener('DOMContentLoaded', (event) => {
    const params = new URLSearchParams(window.location.search);
    const tab = params.get('tab');

    if (tab === 'report-1') {
      const reportsTabTrigger = document.querySelector('a[data-bs-toggle="tab"][href="#report-1"]');
      if (reportsTabTrigger) {
        const tabInstance = new bootstrap.Tab(reportsTabTrigger);
        tabInstance.show();
      }
    }
  });

  //Script to open interval_time according to interval_unit in dropdown
   const intervalUnitSelect = document.getElementById('interval_unit');
   const intervalTimeSelect = document.getElementById('interval_time');

    intervalUnitSelect.addEventListener('change', function() {
        const selectedUnit = this.value;
        intervalTimeSelect.innerHTML = '<option value="">Select</option>'; // Reset options

        if (selectedUnit === 'second') {
            intervalTimeSelect.innerHTML += '<option value="30">30 seconds</option>';
            intervalTimeSelect.innerHTML += '<option value="50">50 seconds</option>';
        } else if (selectedUnit === 'minute') {
            intervalTimeSelect.innerHTML += '<option value="10">10 minutes</option>';
             intervalTimeSelect.innerHTML += '<option value="20">20 minutes</option>';
              intervalTimeSelect.innerHTML += '<option value="30">30 minutes</option>';
               intervalTimeSelect.innerHTML += '<option value="40">40 minutes</option>';
            intervalTimeSelect.innerHTML += '<option value="50">50 minutes</option>';
        } else if (selectedUnit === 'hour') {
            intervalTimeSelect.innerHTML += '<option value="1">1 hour</option>';
            intervalTimeSelect.innerHTML += '<option value="3">3 hours</option>';
            intervalTimeSelect.innerHTML += '<option value="6">6 hours</option>';
            intervalTimeSelect.innerHTML += '<option value="12">12 hours</option>';
            intervalTimeSelect.innerHTML += '<option value="24">24 hours</option>';
        }
    });
$("#execute_regular").on("click", function () {

              let domain = $("#domain").val().trim();
              let query_type = $("#query_type").val().trim();
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
                "query_type":query_type,
                "anchor":anchor,
                 "zone":zone
            }
               $.ajax({
                url: `/generate-ping-query/`,
                method: "POST",
                headers: {'X-CSRFToken': document.getElementById('csrf').querySelector('input').value},
                data: mydata,
                beforeSend: function() {
                // Show loader before the request starts
                Swal.fire({
                    title: 'Processing ping...',
                    text: 'Please wait....',
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
                            text: 'Ping Query Executed successfully.',
                            icon: 'success',
                            confirmButtonText: 'OK'
                        }).then(() => {
                             window.location.href = '/ping-command/';
                        });

                    } else {
                        showError(response.error || "Failed to add ping!");
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


 $("#execute_periodic").on("click", function () {

              let domain = $("#domain_time_range").val().trim();
              let query_type = $("#query_type_periodic").val().trim();
              let anchor = $("#anchor_time").val().trim();
              let interval_unit = $("#interval_unit").val().trim();
              let interval_time = $("#interval_time").val().trim();
              let time_unit = $("#time_unit").val().trim();
              let time = $("#time").val().trim();
              let zone = $("#zone_time").val().trim();
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
                "query_type":query_type,
                "anchor":anchor,
                   "interval_unit":interval_unit,
                   "interval_time":interval_time,
                   "time_unit":time_unit,
                   "time":time,
                   "zone":zone
            }

               $.ajax({
              url: `/generate-ping-query/`,
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
                            text: 'PING Query Executed successfully.',
                            icon: 'success',
                            confirmButtonText: 'OK'
                        }).then(() => {
                            window.location.href = '/ping-command/';
                        });

                    } else {
                        showError(response.error || "Failed to add domain!");
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
          })