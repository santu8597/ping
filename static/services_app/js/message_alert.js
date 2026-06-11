$(document).ready(function () {
    $(".close-btn").on("click", function () {
        const message = $(this).closest("li");

        // Add slide-out animation
        message.css({
            animation: "slide-out 0.5s forwards",
        });

        // Remove the element after the animation
        setTimeout(function () {
            message.remove();
        }, 500); // Match the duration of the animation
    });
});