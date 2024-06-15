class onFocus {
    constructor() {
        this.run = this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.addFocusClass();
            this.keyUpObserve();
            this.clickLink();
            this.initialLabelState();
            this.setInitialFormState();  // Added method to set initial form state
        });
        return 0;
    }

    addFocusClass() {
        const formControls = document.querySelectorAll('.form-control');
        
        formControls.forEach(control => {
            control.addEventListener('focus', function () {
                control.classList.add('on-focus');
                const previousElement = control.previousElementSibling;
                if (previousElement && previousElement.classList.contains('form-label')) {
                    previousElement.classList.add('on-focus');
                }
            });

            control.addEventListener('focusout', function () {
                control.classList.remove('on-focus');
                const previousElement = control.previousElementSibling;
                if (previousElement && previousElement.classList.contains('form-label')) {
                    previousElement.classList.remove('on-focus');
                }
            });
        });
    }

    keyUpObserve() {
        const formControls = document.querySelectorAll('.form-control');
        
        formControls.forEach(control => {
            control.addEventListener('keyup', function () {
                const previousElement = control.previousElementSibling;
                if (previousElement && previousElement.classList.contains('form-label')) {
                    if (control.value.length > 0) {
                        previousElement.classList.add('filled');
                    } else {
                        previousElement.classList.remove('filled');
                    }
                }
            });
        });
    }

    initialLabelState() {
        const formControls = document.querySelectorAll('.form-control');

        formControls.forEach(control => {
            const previousElement = control.previousElementSibling;
            if (previousElement && previousElement.classList.contains('form-label')) {
                if (control.value.length > 0) {
                    previousElement.classList.add('filled');
                }
            }
        });
    }

    clickLink() {
        const links = document.querySelectorAll('.link');
        
        links.forEach(link => {
            link.addEventListener('click', function (event) {
                event.preventDefault();
                
                const openId = link.getAttribute('data-open');
                const closeId = link.getAttribute('data-close');
                
                const closeElement = document.getElementById(closeId);
                const openElement = document.getElementById(openId);
                
                if (closeElement && openElement) {
                    closeElement.style.opacity = '0';
                    closeElement.style.top = '100px';

                    setTimeout(() => {
                        closeElement.classList.remove('open');
                        closeElement.classList.add('close');
                        closeElement.removeAttribute('style');

                        openElement.classList.remove('close');
                        openElement.classList.add('open');
                    }, 500);
                }
            });
        });
    }

    setInitialFormState() {
        const activeForm = "{{ active_form }}";
        if (activeForm === "signup") {
            document.getElementById('login-page').classList.remove('open');
            document.getElementById('login-page').classList.add('close');
            document.getElementById('new-account-page').classList.remove('close');
            document.getElementById('new-account-page').classList.add('open');
        }
    }
}

const run = new onFocus();

document.addEventListener('DOMContentLoaded', function () {
    const passwordInputs = [
        { inputId: 'sign-in-password-input', checkboxId: 'sign-in-show-password-checkbox' },
        { inputId: 'sign-up-password-input', checkboxId: 'sign-up-show-password-checkbox' },
        { inputId: 'confirm-password-input', checkboxId: 'confirm-show-password-checkbox' }
    ];

    passwordInputs.forEach(({ inputId, checkboxId }) => {
        const passwordInput = document.getElementById(inputId);
        const showPasswordCheckbox = document.getElementById(checkboxId);
        
        if (passwordInput && showPasswordCheckbox) {
            showPasswordCheckbox.addEventListener('change', function () {
                if (this.checked) {
                    passwordInput.type = 'text';
                } else {
                    passwordInput.type = 'password';
                }
            });
        }
    });
});
