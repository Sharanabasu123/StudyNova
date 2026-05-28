document.addEventListener('DOMContentLoaded', function() {
    // Loader
    const loader = document.querySelector('.loader-wrapper');
    if (loader) {
        setTimeout(() => {
            loader.style.opacity = '0';
            setTimeout(() => {
                loader.style.visibility = 'hidden';
            }, 500);
        }, 1000);
    }

    // Typing Effect
    const typedElement = document.getElementById('typed');
    if (typedElement && window.Typed) {
        new Typed('#typed', {
            strings: [
                'Learn Smarter, Grow Faster 🚀',
                'Upload Your Notes 📚',
                'Access Quality Study Materials 🎓',
                'Empowering Students Everywhere ✨'
            ],
            typeSpeed: 50,
            backSpeed: 30,
            loop: true
        });
    }

    // Navbar Scroll Effect
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.style.padding = '10px 0';
                navbar.style.background = 'rgba(255, 255, 255, 0.98)';
            } else {
                navbar.style.padding = '15px 0';
                navbar.style.background = 'rgba(255, 255, 255, 0.95)';
            }
        });
    }

    // Form Validation and Animations
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Smooth Scroll
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const target = this.getAttribute('href');
            if (!target || target === '#') {
                return;
            }
            const targetElement = document.querySelector(target);
            if (!targetElement) {
                return;
            }
            e.preventDefault();
            targetElement.scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    if (window.AOS) {
        AOS.init({
            duration: 1000,
            once: true
        });
    }
});
