// Grab the overlay
const loader = document.getElementById("app-loader");

// 1) Hide the loader once on initial page load
window.addEventListener("load", () => {
  loader.style.display = "none";
});

// 2) Define show/hide helpers
function showLoader() {
  loader.style.display = "flex";
}
function hideLoader() {
  loader.style.display = "none";
}

// 3) Bind to link clicks (internal only)
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("a").forEach(link => {
    const href = link.getAttribute("href") || "";
    if (href.startsWith("/") && !href.startsWith("#") && !link.hasAttribute("target")) {
      link.addEventListener("click", showLoader);
    }
  });

  // Bind to form submissions
  document.querySelectorAll("form").forEach(form => {
    form.addEventListener("submit", showLoader);
  });
// // 4) Bind to jQuery AJAX events (requires jQuery)
//   if (window.jQuery) {
//     $(document)
//       .on("ajaxStart", showLoader)
//       .on("ajaxStop ajaxError", hideLoader);
//   }

// 4) Bind to jQuery AJAX events (requires jQuery)
if (window.jQuery) {
  // When any AJAX starts, check if it should show loader or not
  $(document).on("ajaxSend", function (event, jqXHR, options) {
    if (options && options.noLoader === true) {
      // Mark request as no-loader → so ajaxStop won't hide globally incorrectly
      jqXHR._skipLoader = true;
      return;
    }
    showLoader();
  });

  // Hide loader only if it was shown for this request
  $(document).on("ajaxComplete ajaxError", function (event, jqXHR) {
    if (!jqXHR._skipLoader) {
      hideLoader();
    }
  });
}


  // 5) Wrap fetch if used
//   if (window.fetch) {
//     const originalFetch = window.fetch;
//     window.fetch = async (...args) => {
//       showLoader();
//       try {
//         return await originalFetch(...args);
//       } finally {
//         hideLoader();
//       }
// };
//   }

if (window.fetch) {
  const originalFetch = window.fetch;
  window.fetch = async (input, init = {}) => {

    // If request contains noLoader flag → don't show the loader
    if (init && init.noLoader === true) {
      return originalFetch(input, init);
    }

    showLoader();
    try {
      return await originalFetch(input, init);
    } finally {
      hideLoader();
    }
  };
}



});

window.addEventListener("pageshow", () => {
  // console.log("Pageshow");
  loader.style.display = "none";
});
