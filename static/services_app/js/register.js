document.addEventListener('DOMContentLoaded', function () {


    // Add red asterisk to required fields
    document.querySelectorAll('label').forEach(function(label) {
        const inputId = label.getAttribute('for');
        const input = document.getElementById(inputId);
        if (input && input.hasAttribute('required')) {
            const asterisk = document.createElement('span');
            asterisk.textContent = ' *';
            asterisk.style.color = 'red';
            label.appendChild(asterisk);
        }
    });
    // Email input listener
    const emailInput = document.getElementById('email');
    const sendOtpBtn = document.getElementById('send-otp-btn');
    const resendOtpBtn = document.getElementById('resend_otp');
    const emailStatus = document.getElementById('email-status');

    if (emailInput && sendOtpBtn && emailStatus) {
        emailInput.addEventListener('input', function () {
            const emailVal = emailInput.value.trim();
            const isValidEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailVal);

            if (isValidEmail) {
                sendOtpBtn.style.display = 'inline-block';
                sendOtpBtn.disabled = false;

                // resendOtpBtn.style.display = 'inline-block';
                // resendOtpBtn.disabled = false;
            } else {
                sendOtpBtn.style.display = 'none';
                sendOtpBtn.disabled = true;

                // resendOtpBtn.style.display = 'none';
                // resendOtpBtn.disabled = true;
            }
        });
    }

      // Mobile input listener
    const mobileInput = document.getElementById('mobile');
    const sendmobileOtpBtn = document.getElementById('send-mobile-otp-btn');
    const mobileStatus = document.getElementById('mobile-status');

   if (mobileInput && sendmobileOtpBtn && mobileStatus) {
    mobileInput.addEventListener('input', function () {
        formatNumber(mobileInput);  // This still formats the number

        const value = mobileInput.value;
        const isValidMobile = /^\d{10}$/.test(value);  // Check for exactly 10 digits

        if (isValidMobile) {
            sendmobileOtpBtn.style.display = 'inline-block';
            sendmobileOtpBtn.disabled = false;
            mobileStatus.style.display = 'block'; // Optional: show status section
        } else {
            sendmobileOtpBtn.style.display = 'none';
            sendmobileOtpBtn.disabled = true;
            mobileStatus.style.display = 'none';
        }
    });
}

});

function formatNumber(input) {
        // Remove all non-numeric characters
        let value = input.value.replace(/\D/g, '');

        // Limit the value to exactly 10 digits
        if (value.length > 10) {
            value = value.substring(0, 10);
        }

        // Update the input value with the limited value
        input.value = value;
    }

function sendOTP() {
    const emailField = document.getElementById('email');
    const emailStatusField = document.getElementById('email-status');
    const emailValue = emailField.value.trim();

    const resendOtpBtn = document.getElementById('resend_otp');
    const sendOtpBtn = document.getElementById('send-otp-btn');

    // Check if the email is valid and not already verified
    if (emailStatusField.value === 'valid' && emailValue === emailStatusField.getAttribute('data-email')) {
        // If email is valid and already matches the stored email, no need to send OTP again
        Swal.fire({
            icon: 'info',
            title: 'Email Already Verified',
            text: 'Your email is already verified. No need to send OTP again.',
        });
        return;
    }

    // Show loader before the request starts
    Swal.fire({
        title: 'Processing...',
        text: 'Please wait while sending the OTP.',
        onBeforeOpen: () => {
            Swal.showLoading();
        },
        allowOutsideClick: false, // Prevent closing the loader by clicking outside
        showConfirmButton: false, // Hide the confirm button
    });

    // Prepare the data to be sent to the backend
    const data = {
        email: emailValue,
    };

    // Send AJAX request to the backend
    fetch('/api/common/otp/send/', {
        method: 'POST',
        headers: {'X-CSRFToken': document.getElementById('csrf').querySelector('input').value},
        body: JSON.stringify(data), // Send the email in the body of the request
    })
    .then(response => response.json())
    .then(data => {
        // Hide the loader after the response is received
        Swal.close();
        if (data.status === 'success') {
            // If OTP is sent successfully, show success message
            Swal.fire({
                icon: 'success',
                title: 'OTP Sent Successfully.',
                text: data.message, // The success message from the backend
            });

            sendOtpBtn.classList.add("disabled");

            resendOtpBtn.style.display = 'inline-block';
            resendOtpBtn.disabled = false;
            resendOtpBtn.classList.remove("disabled");


            // Show OTP input field and "Verify OTP" button
            document.getElementById('otp-section').style.display = 'block';
            document.getElementById('verify-otp-btn').disabled = false; // Enable "Verify OTP" button
            document.getElementById('send-otp-btn').style.display = 'none'; // Hide the "Send OTP" button after it's sent
        } else if (data.status === 'error') {
            // If there's an error message, show it
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.message, // The error message from the backend
            });
        }
    })
    .catch(error => {
        // If there's a network or other error, handle it here
        console.error('Error sending OTP:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error - '+ error,
            text: 'An error occurred while sending the OTP. Please try again later.',
        });
    });
}

function verifyOTP() {
    const emailField = document.getElementById('email');
    const otpField = document.getElementById('otp');
    const otpValue = otpField.value.trim();
    const emailValue = emailField.value.trim();
    const resendOtpBtn = document.getElementById('resend_otp');

    if (!emailValue || !otpValue) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Please provide both email and OTP.',
        });
        return;
    }

    // Show loader before the request starts
    Swal.fire({
        title: 'Processing...',
        text: 'Validating OTP. Please wait.',
        onBeforeOpen: () => {
            Swal.showLoading();
        },
        allowOutsideClick: false, // Prevent closing the loader by clicking outside
        showConfirmButton: false, // Hide the confirm button
    });

    fetch('/api/common/otp/validate/', {
        method: 'POST',
        headers: {'X-CSRFToken': document.getElementById('csrf').querySelector('input').value},
        body: JSON.stringify({
            email: emailValue,
            otp: otpValue,
        }),
    })
    .then(response => response.json())
    .then(data => {
        // Hide the loader after the response is received
        Swal.close();

        if (data.status === 'success') {
           // OTP is correct, show success alert
            Swal.fire({
                icon: 'success',
                title: 'Email Verified',
                text: 'Your email has been successfully verified.',
            }).then(() => {
                // Hide the OTP section after successful verification
                document.getElementById('email').readOnly = true;
                document.getElementById('email').style.backgroundColor = 'aliceblue';
                document.getElementById('otp-section').style.display = 'none';
                document.getElementById('otp').value = ''; // Clear OTP input field
                resendOtpBtn.style.display = 'none';

                // Disable the "Verify OTP" button after success
                document.getElementById('verify-otp-btn').disabled = true;

                // Hide the "Send OTP" button and prevent future OTP sending until email is changed
                document.getElementById('send-otp-btn').style.display = 'none';

                // Update the email-status field to "valid" and store the new email in data-email
                const emailStatusField = document.getElementById('email-status');
                emailStatusField.value = 'valid'; // Set status to valid
                emailStatusField.setAttribute('data-email', emailValue); // Update data-email with the new email

            });

        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.message || 'Failed to validate OTP. Please try again.',
            });
        }
    })
    .catch(error => {
        // Hide the loader if an error occurs
        Swal.close();

        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Failed to validate OTP. Please try again later.',
        });
        console.error('Error:', error);
    });
}



function sendmobileOTP(resend=false) {
    const phoneField = document.getElementById('mobile');
    const phoneStatusField = document.getElementById('mobile-status');
    const phoneValue = phoneField.value.trim();

    const resendOtpBtn = document.getElementById('resend_mobile_otp');
    const sendOtpBtn = document.getElementById('send-mobile-otp-btn');

    // Check if the phone is valid and not already verified
    if (phoneStatusField.value === 'valid' && phoneValue === phoneStatusField.getAttribute('data-mobile')) {
        // If email is valid and already matches the stored email, no need to send OTP again
        Swal.fire({
            icon: 'info',
            title: 'Phone Number Already Verified',
            text: 'Your number is already verified. No need to send OTP again.',
        });
        return;
    }

    // Show loader before the request starts
    Swal.fire({
        title: 'Processing...',
        text: 'Please wait while sending the OTP.',
        onBeforeOpen: () => {
            Swal.showLoading();
        },
        allowOutsideClick: false, // Prevent closing the loader by clicking outside
        showConfirmButton: false, // Hide the confirm button
    });

    // Prepare the data to be sent to the backend
    const data = {
        mobile: phoneValue,
    };

    // Send AJAX request to the backend
    fetch('/api/common/mobile/otp/send/', {
        method: 'POST',
        headers: {'X-CSRFToken': document.getElementById('csrf').querySelector('input').value},
        body: JSON.stringify(data), // Send the email in the body of the request
    })
    .then(response => response.json())
    .then(data => {
        // Hide the loader after the response is received
        Swal.close();
        if (data.status === 'success') {
            // If OTP is sent successfully, show success message
            Swal.fire({
                icon: 'success',
                title: 'OTP Sent Successfully.',
                text: data.message, // The success message from the backend
            });

            sendOtpBtn.classList.add("disabled");

            resendOtpBtn.style.display = 'inline-block';
            if (!resend){
                 resendOtpBtn.disabled = false;
                 resendOtpBtn.classList.remove("disabled");
            }

            // Show OTP input field and "Verify OTP" button
            document.getElementById('otp-mobile-section').style.display = 'block';
            document.getElementById('verify-mobile-otp-btn').disabled = false; // Enable "Verify OTP" button
            document.getElementById('send-mobile-otp-btn').style.display = 'none'; // Hide the "Send OTP" button after it's sent
        } else if (data.status === 'error') {
            // If there's an error message, show it
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.message, // The error message from the backend
            });
        }
    })
    .catch(error => {
        // If there's a network or other error, handle it here
        console.error('Error sending OTP:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error - '+ error,
            text: 'An error occurred while sending the OTP. Please try again later.',
        });
    });
}
function verifymobileOTP() {
    const phoneField = document.getElementById('mobile');
    const otpField = document.getElementById('mobile_otp');
    const otpValue = otpField.value.trim();
    const phoneValue = phoneField.value.trim();

    if (!phoneValue || !otpValue) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Please provide both number and OTP.',
        });
        return;
    }

    // Show loader before the request starts
    Swal.fire({
        title: 'Processing...',
        text: 'Validating OTP. Please wait.',
        onBeforeOpen: () => {
            Swal.showLoading();
        },
        allowOutsideClick: false, // Prevent closing the loader by clicking outside
        showConfirmButton: false, // Hide the confirm button
    });

    fetch('/api/common/mobile/otp/validate/', {
        method: 'POST',
        headers: {'X-CSRFToken': document.getElementById('csrf').querySelector('input').value},
        body: JSON.stringify({
            mobile: phoneValue,
            otp: otpValue,
        }),
    })
    .then(response => response.json())
    .then(data => {
        // Hide the loader after the response is received
        Swal.close();

        if (data.status === 'success') {
           // OTP is correct, show success alert
            Swal.fire({
                icon: 'success',
                title: 'Contact Number Verified',
                text: 'Your contact number has been successfully verified.',
            }).then(() => {
                // Hide the OTP section after successful verification
                document.getElementById('mobile').readOnly = true;
                document.getElementById('mobile').style.backgroundColor = 'aliceblue';
                document.getElementById('otp-mobile-section').style.display = 'none';
                document.getElementById('mobile_otp').value = ''; // Clear OTP input field

                // Disable the "Verify OTP" button after success
                document.getElementById('verify-mobile-otp-btn').disabled = true;

                // Hide the "Send OTP" button and prevent future OTP sending until email is changed
                document.getElementById('send-mobile-otp-btn').style.display = 'none';

                // Update the email-status field to "valid" and store the new email in data-email
                const mobileStatusField = document.getElementById('mobile-status');
                mobileStatusField.value = 'valid'; // Set status to valid
                mobileStatusField.setAttribute('data-mobile', phoneValue); // Update data-email with the new email

            });

        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.message || 'Failed to validate OTP. Please try again.',
            });
        }
    })
    .catch(error => {
        // Hide the loader if an error occurs
        Swal.close();

        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Failed to validate OTP. Please try again later.',
        });
        console.error('Error:', error);
    });
}


function toggleFields() {
    var role = document.getElementById("role").value;
    var facultyFields = document.getElementById("facultyFields");
    var userFields = document.getElementById("userFields");

    if (role === "faculty") {
        facultyFields.style.display = "flex";
        userFields.style.display = "none";
    } else if (role === "user") {
        facultyFields.style.display = "none";
        userFields.style.display = "flex";
    } else {
        facultyFields.style.display = "none";
        userFields.style.display = "none";
    }
}