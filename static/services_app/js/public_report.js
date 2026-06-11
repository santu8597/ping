document.addEventListener("DOMContentLoaded", function () {

        $(document).on("change", ".togglePublic", function () {

            let isPublic = $(this).prop("checked");
            let id = $(this).data("id");

            let mydata = {
                "id": parseInt(id),
                "is_public": isPublic
            };
            console.log("Toggle Public :", mydata);

            $.ajax({
                url: "/public-report/",
                type: "POST",
                headers: {
                    "X-CSRFToken": document.getElementById("csrf").querySelector("input").value
                },
                data: mydata,
                success: function (response) {
                    if (response.status == 1) {
                        if (isPublic) {
                            Swal.fire({
                                title: "Success!",
                                text: "Report is now Public.",
                                icon: "success",
                                confirmButtonText: "OK"
                            });
                        } else {
                            Swal.fire({
                                title: "Updated!",
                                text: "Report is now Private.",
                                icon: "info",
                                confirmButtonText: "OK"
                            });
                        }
                    } else {
                        showError(response.msg || "Failed to update report visibility!");
                    }
                },
                error: function () {
                    showError("Something went wrong! Please try again.");
                }
            });
        });
        function showError(message) {
            Swal.fire({
                icon: "error",
                title: "Error",
                text: message,
                confirmButtonColor: "#d33"
            });
        }

    });




// For individual pages
document.addEventListener("DOMContentLoaded", function () {

    $("#submit_manage_query_btn").on("click", function () {
        let queryId = $("#manage_query_id").val().trim();
        let isPublic = $("#manage_public_private").val();

        if (!isPublic) {
            Swal.fire({
                icon: "warning",
                title: "MissingQuery visibility",
                text: "Please select public or private before saving.",
                confirmButtonColor: "#3085d6"
            });
            return;
        }

        let mydata = {
            "id": parseInt(queryId),
            "is_public": (isPublic === "true")
        };
        console.log("Modal Individual Page Data:", mydata);

        $.ajax({
            url: "/public-report/",
            type: "POST",
            headers: {
                "X-CSRFToken": document.getElementById("csrf").querySelector("input").value
            },
            data: mydata,
            success: function (response) {
                if (response.status == 1) {
                    Swal.fire({
                        title: "Success!",
                        text: mydata.is_public
                              ? "Measurement is now Public and visible in AIORI’s Public Measurements section."
                              : "Measurement is now Private.",
                        icon: mydata.is_public ? "success" : "info",
                        confirmButtonText: "OK"
                    }).then(() => {
                        $("#publicModal").modal("hide");
                        location.reload();
                    });
                } else {
                    showError(response.msg || "Failed to update measurement visibility!");
                }
            },
            error: function () {
                showError("Something went wrong! Please try again.");
            }
        });
    });

    function showError(message) {
        Swal.fire({
            icon: "error",
            title: "Error",
            text: message,
            confirmButtonColor: "#d33"
        });
    }

});

