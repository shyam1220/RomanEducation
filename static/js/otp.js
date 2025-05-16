// OTP handling functionality
document.addEventListener('DOMContentLoaded', function() {
    const otpInput = document.getElementById('otp');
    
    if (otpInput) {
        // Auto focus on OTP input
        otpInput.focus();
        
        // Only allow numbers in OTP field
        otpInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
        });
        
        // Auto submit when 6 digits are entered
        otpInput.addEventListener('keyup', function() {
            if (this.value.length === 6) {
                const form = this.closest('form');
                if (form) {
                    // Add a small delay before submitting
                    setTimeout(() => {
                        form.submit();
                    }, 500);
                }
            }
        });
        
        // Add timer for OTP expiration (10 minutes)
        const timerElement = document.createElement('div');
        timerElement.className = 'text-center mt-3';
        timerElement.innerHTML = '<small class="text-muted">OTP expires in: <span id="timer">10:00</span></small>';
        
        const formElement = otpInput.closest('form');
        if (formElement) {
            formElement.insertAdjacentElement('afterend', timerElement);
            
            // Set the timer
            let timeLeft = 10 * 60; // 10 minutes in seconds
            const timerDisplay = document.getElementById('timer');
            
            const countdownTimer = setInterval(function() {
                const minutes = Math.floor(timeLeft / 60);
                let seconds = timeLeft % 60;
                seconds = seconds < 10 ? '0' + seconds : seconds;
                
                timerDisplay.textContent = `${minutes}:${seconds}`;
                timeLeft--;
                
                if (timeLeft < 0) {
                    clearInterval(countdownTimer);
                    timerDisplay.textContent = 'Expired';
                    timerDisplay.classList.add('text-danger');
                    
                    // Disable the OTP input and submit button
                    otpInput.disabled = true;
                    const submitButton = formElement.querySelector('button[type="submit"]');
                    if (submitButton) {
                        submitButton.disabled = true;
                        submitButton.innerHTML = '<i class="fas fa-clock"></i> OTP Expired';
                    }
                    
                    // Show message
                    const expiredMsg = document.createElement('div');
                    expiredMsg.className = 'alert alert-warning mt-3';
                    expiredMsg.innerHTML = 'Your OTP has expired. Please request a new one.';
                    formElement.insertAdjacentElement('afterend', expiredMsg);
                }
            }, 1000);
        }
    }
});