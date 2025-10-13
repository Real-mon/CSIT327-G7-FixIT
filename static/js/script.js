// FixIT System - Custom JavaScript

// Document Ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('FixIT System Loaded');
    
    // Initialize tooltips
    initializeTooltips();
    
    // Auto-hide alerts after 5 seconds
    autoHideAlerts();
    
    // Form validation enhancement
    enhanceFormValidation();
    
    // Add smooth scrolling
    smoothScrolling();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Auto-hide alert messages after 5 seconds
 */
function autoHideAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

/**
 * Enhance form validation with visual feedback
 */
function enhanceFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(function(input) {
            input.addEventListener('blur', function() {
                if (input.value.trim() !== '') {
                    if (input.checkValidity()) {
                        input.classList.remove('is-invalid');
                        input.classList.add('is-valid');
                    } else {
                        input.classList.remove('is-valid');
                        input.classList.add('is-invalid');
                    }
                }
            });
        });
    });
}

/**
 * Add smooth scrolling behavior
 */
function smoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Show loading spinner on form submit
 */
function showLoadingSpinner(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
    button.disabled = true;
    
    return {
        hide: function() {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    };
}

/**
 * Confirm before logout
 */
function confirmLogout() {
    return confirm('Are you sure you want to logout?');
}

/**
 * Password strength checker
 */
function checkPasswordStrength(password) {
    let strength = 0;
    
    // Check length
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    
    // Check for lowercase
    if (/[a-z]/.test(password)) strength++;
    
    // Check for uppercase
    if (/[A-Z]/.test(password)) strength++;
    
    // Check for numbers
    if (/\d/.test(password)) strength++;
    
    // Check for special characters
    if (/[^a-zA-Z\d]/.test(password)) strength++;
    
    return {
        strength: strength,
        text: strength < 2 ? 'Weak' : strength < 4 ? 'Medium' : 'Strong',
        class: strength < 2 ? 'danger' : strength < 4 ? 'warning' : 'success'
    };
}

/**
 * Display password strength indicator
 */
function displayPasswordStrength(inputId, displayId) {
    const passwordInput = document.getElementById(inputId);
    const displayElement = document.getElementById(displayId);
    
    if (passwordInput && displayElement) {
        passwordInput.addEventListener('input', function() {
            const result = checkPasswordStrength(this.value);
            displayElement.innerHTML = `
                <small class="text-${result.class}">
                    Password Strength: ${result.text}
                </small>
            `;
        });
    }
}

/**
 * Format phone number input
 */
function formatPhoneNumber(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length > 0) {
        if (value.length <= 3) {
            value = value;
        } else if (value.length <= 6) {
            value = value.slice(0, 3) + '-' + value.slice(3);
        } else {
            value = value.slice(0, 3) + '-' + value.slice(3, 6) + '-' + value.slice(6, 10);
        }
    }
    input.value = value;
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        alert('Copied to clipboard!');
    }).catch(function(err) {
        console.error('Failed to copy: ', err);
    });
}

/**
 * Show confirmation modal
 */
function showConfirmModal(title, message, onConfirm) {
    const modalHtml = `
        <div class="modal fade" id="confirmModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        ${message}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="confirmButton">Confirm</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
    
    document.getElementById('confirmButton').addEventListener('click', function() {
        onConfirm();
        modal.hide();
    });
    
    modal.show();
}