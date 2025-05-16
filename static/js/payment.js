// Payment processing functionality
document.addEventListener('DOMContentLoaded', function() {
    const paymentForm = document.getElementById('paymentForm');
    
    if (paymentForm) {
        // Format credit card number with spaces
        const cardNumberInput = document.getElementById('cardNumber');
        if (cardNumberInput) {
            cardNumberInput.addEventListener('input', function(e) {
                // Remove non-digits
                let value = this.value.replace(/\D/g, '');
                // Limit to 16 digits
                value = value.substring(0, 16);
                // Add spaces after every 4 digits
                value = value.replace(/(\d{4})(?=\d)/g, '$1 ');
                // Update the input value
                this.value = value;
            });
        }
        
        // Format expiration date
        const expDateInput = document.getElementById('expDate');
        if (expDateInput) {
            expDateInput.addEventListener('input', function(e) {
                // Remove non-digits
                let value = this.value.replace(/\D/g, '');
                // Limit to 4 digits
                value = value.substring(0, 4);
                // Add slash after first 2 digits
                if (value.length > 2) {
                    value = value.substring(0, 2) + '/' + value.substring(2);
                }
                // Update the input value
                this.value = value;
            });
        }
        
        // Format CVV - only allow 3 or 4 digits
        const cvvInput = document.getElementById('cvv');
        if (cvvInput) {
            cvvInput.addEventListener('input', function(e) {
                // Remove non-digits
                let value = this.value.replace(/\D/g, '');
                // Limit to 4 digits
                value = value.substring(0, 4);
                // Update the input value
                this.value = value;
            });
        }
        
        // Form validation on submit
        const submitButton = document.getElementById('submitPayment');
        if (submitButton) {
            submitButton.addEventListener('click', function() {
                // Basic validation
                let isValid = true;
                
                // Validate card name
                const cardName = document.getElementById('cardName');
                if (cardName.value.trim().length < 3) {
                    cardName.classList.add('is-invalid');
                    isValid = false;
                } else {
                    cardName.classList.remove('is-invalid');
                }
                
                // Validate card number (should be 16 digits + spaces)
                if (cardNumberInput.value.replace(/\s/g, '').length !== 16) {
                    cardNumberInput.classList.add('is-invalid');
                    isValid = false;
                } else {
                    cardNumberInput.classList.remove('is-invalid');
                }
                
                // Validate expiration date (should be MM/YY format)
                const expRegex = /^(0[1-9]|1[0-2])\/\d{2}$/;
                if (!expRegex.test(expDateInput.value)) {
                    expDateInput.classList.add('is-invalid');
                    isValid = false;
                } else {
                    // Check if date is in the future
                    const [month, year] = expDateInput.value.split('/');
                    const expiryDate = new Date(2000 + parseInt(year), parseInt(month) - 1);
                    const currentDate = new Date();
                    
                    if (expiryDate < currentDate) {
                        expDateInput.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        expDateInput.classList.remove('is-invalid');
                    }
                }
                
                // Validate CVV (should be 3 or 4 digits)
                if (cvvInput.value.length < 3) {
                    cvvInput.classList.add('is-invalid');
                    isValid = false;
                } else {
                    cvvInput.classList.remove('is-invalid');
                }
                
                // Submit form if valid
                if (!isValid) {
                    // Show validation errors
                    const invalidFields = document.querySelectorAll('.is-invalid');
                    if (invalidFields.length > 0) {
                        invalidFields[0].focus();
                    }
                    return false;
                }
                
                // Form is valid - proceed to payment processing
                // The actual payment processing logic is in the template's inline script
            });
        }
    }
});