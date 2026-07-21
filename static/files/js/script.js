/* ============================================================
   ELEGANT EVENTS - GLOBAL JAVASCRIPT
   ============================================================

   TABLE OF CONTENTS
   1.  DOM Ready Wrapper
   2.  Navigation (Mobile Menu)
   3.  LightSlider Initialization
   4.  Scroll Reveal Animations
   5.  Back to Top
   6.  Smooth Scroll
   7.  Navbar Scroll Effects
   8.  Form Validation
   9.  Counter Animations
  10.  Performance Optimizations
  11.  Accessibility Enhancements
============================================================ */

(function() {
    'use strict';

    /* ============================================================
       1. DOM READY WRAPPER
       ============================================================ */

    document.addEventListener('DOMContentLoaded', function() {

        console.log('✨ Elegant Events - Initializing...');

        /* ============================================================
           2. NAVIGATION (Mobile Menu)
           ============================================================ */

        function initMobileMenu() {
            var navbar = document.querySelector('.navbar-collapse');
            var toggler = document.querySelector('.navbar-toggler');

            if (!navbar || !toggler) return;

            // Close mobile menu when clicking outside
            document.addEventListener('click', function(e) {
                if (window.innerWidth <= 992) {
                    var isClickInside = navbar.contains(e.target) || toggler.contains(e.target);
                    if (!isClickInside && navbar.classList.contains('show')) {
                        toggler.click();
                    }
                }
            });

            // Close mobile menu when clicking a link
            var navLinks = navbar.querySelectorAll('.nav-link');
            for (var i = 0; i < navLinks.length; i++) {
                navLinks[i].addEventListener('click', function() {
                    if (window.innerWidth <= 992 && navbar.classList.contains('show')) {
                        toggler.click();
                    }
                });
            }
        }

        /* ============================================================
           3. LIGHTSLIDER INITIALIZATION
           ============================================================ */

        function initSliders() {
            // Check if lightSlider exists and jQuery is available
            if (typeof $ === 'undefined' || typeof $.fn.lightSlider === 'undefined') {
                console.warn('LightSlider not available.');
                return;
            }

            // Testimonial slider
            var testimonialSlider = document.getElementById('testimonial-slider');
            if (testimonialSlider) {
                try {
                    $(testimonialSlider).lightSlider({
                        item: 3,
                        slideMove: 1,
                        speed: 600,
                        auto: true,
                        loop: true,
                        pause: 5000,
                        pauseOnHover: true,
                        controls: true,
                        pager: true,
                        enableTouch: true,
                        enableDrag: true,
                        swipeThreshold: 40,
                        freeMove: true,
                        keyPress: true,
                        responsive: [
                            {
                                breakpoint: 992,
                                settings: { item: 2, slideMove: 1 }
                            },
                            {
                                breakpoint: 576,
                                settings: { item: 1, slideMove: 1 }
                            }
                        ]
                    });
                    console.log('✅ Testimonial slider initialized.');
                } catch (e) {
                    console.warn('Testimonial slider failed:', e);
                }
            }

            // Gallery slider
            var gallerySlider = document.getElementById('gallery-slider');
            if (gallerySlider) {
                try {
                    $(gallerySlider).lightSlider({
                        item: 4,
                        slideMove: 1,
                        speed: 600,
                        auto: true,
                        loop: true,
                        pause: 4000,
                        pauseOnHover: true,
                        controls: true,
                        pager: true,
                        enableTouch: true,
                        enableDrag: true,
                        swipeThreshold: 40,
                        freeMove: true,
                        keyPress: true,
                        responsive: [
                            {
                                breakpoint: 992,
                                settings: { item: 3, slideMove: 1 }
                            },
                            {
                                breakpoint: 768,
                                settings: { item: 2, slideMove: 1 }
                            },
                            {
                                breakpoint: 480,
                                settings: { item: 1, slideMove: 1 }
                            }
                        ]
                    });
                    console.log('✅ Gallery slider initialized.');
                } catch (e) {
                    console.warn('Gallery slider failed:', e);
                }
            }

            // Auto-width slider (for services/packages)
            var autoWidthSlider = document.querySelector('.autoWidth');
            if (autoWidthSlider) {
                try {
                    $(autoWidthSlider).lightSlider({
                        autoWidth: true,
                        loop: true,
                        onSliderLoad: function() {
                            $(autoWidthSlider).removeClass('cS-hidden');
                        }
                    });
                    console.log('✅ Auto-width slider initialized.');
                } catch (e) {
                    console.warn('Auto-width slider failed:', e);
                }
            }
        }

        /* ============================================================
           4. SCROLL REVEAL ANIMATIONS
           ============================================================ */

        function initScrollReveal() {
            var revealElements = document.querySelectorAll('.reveal, .fade-up');

            if (!revealElements.length) return;

            var observer;

            if ('IntersectionObserver' in window) {
                observer = new IntersectionObserver(function(entries) {
                    for (var i = 0; i < entries.length; i++) {
                        if (entries[i].isIntersecting) {
                            entries[i].target.classList.add('visible');
                            observer.unobserve(entries[i].target);
                        }
                    }
                }, {
                    threshold: 0.15,
                    rootMargin: '0px 0px -50px 0px'
                });

                for (var j = 0; j < revealElements.length; j++) {
                    observer.observe(revealElements[j]);
                }
            } else {
                // Fallback for older browsers
                function checkVisibility() {
                    for (var k = 0; k < revealElements.length; k++) {
                        var el = revealElements[k];
                        var rect = el.getBoundingClientRect();
                        var windowHeight = window.innerHeight || document.documentElement.clientHeight;
                        if (rect.top < windowHeight - 80) {
                            el.classList.add('visible');
                        }
                    }
                }

                checkVisibility();
                window.addEventListener('scroll', checkVisibility);
                window.addEventListener('resize', checkVisibility);
            }
        }

        /* ============================================================
           5. BACK TO TOP BUTTON
           ============================================================ */

        function initBackToTop() {
            var btn = document.getElementById('back-to-top');

            if (!btn) return;

            function toggleButton() {
                var scroll = window.pageYOffset || document.documentElement.scrollTop;
                if (scroll > 400) {
                    btn.classList.add('visible');
                } else {
                    btn.classList.remove('visible');
                }
            }

            window.addEventListener('scroll', toggleButton);

            btn.addEventListener('click', function(e) {
                e.preventDefault();
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            });
        }

        /* ============================================================
           6. SMOOTH SCROLL (Anchor links)
           ============================================================ */

        function initSmoothScroll() {
            var anchors = document.querySelectorAll('a[href^="#"]');

            for (var i = 0; i < anchors.length; i++) {
                anchors[i].addEventListener('click', function(e) {
                    var targetId = this.getAttribute('href');
                    if (targetId === '#') return;

                    var target = document.querySelector(targetId);
                    if (target) {
                        e.preventDefault();
                        var navbarHeight = document.querySelector('.navbar-header') ?
                            document.querySelector('.navbar-header').offsetHeight : 0;
                        var targetPosition = target.getBoundingClientRect().top +
                            window.pageYOffset - navbarHeight - 20;

                        window.scrollTo({
                            top: targetPosition,
                            behavior: 'smooth'
                        });
                    }
                });
            }
        }

        /* ============================================================
           7. NAVBAR SCROLL EFFECTS
           ============================================================ */

        function initNavbarScroll() {
            var navbar = document.querySelector('.navbar-header');

            if (!navbar) return;

            function handleScroll() {
                var scroll = window.pageYOffset || document.documentElement.scrollTop;
                if (scroll > 50) {
                    navbar.classList.add('scrolled');
                } else {
                    navbar.classList.remove('scrolled');
                }
            }

            window.addEventListener('scroll', handleScroll);
            handleScroll(); // Check on load
        }

        /* ============================================================
           8. FORM VALIDATION
           ============================================================ */

        function initFormValidation() {
            var forms = document.querySelectorAll('.needs-validation');

            for (var i = 0; i < forms.length; i++) {
                forms[i].addEventListener('submit', function(e) {
                    if (!this.checkValidity()) {
                        e.preventDefault();
                        e.stopPropagation();
                    }
                    this.classList.add('was-validated');
                });
            }
        }

        /* ============================================================
           9. COUNTER ANIMATIONS
           ============================================================ */

        function initCounters() {
            var counters = document.querySelectorAll('.counter');

            if (!counters.length) return;

            var animated = false;
            var observer;

            function animateCounter(el) {
                var target = parseInt(el.getAttribute('data-target'), 10);
                if (isNaN(target)) return;

                var duration = 2000;
                var startTime = performance.now();

                function update(currentTime) {
                    var progress = Math.min((currentTime - startTime) / duration, 1);
                    var value = Math.floor(progress * target);
                    el.textContent = value.toLocaleString();
                    if (progress < 1) {
                        requestAnimationFrame(update);
                    } else {
                        el.textContent = target.toLocaleString();
                    }
                }
                requestAnimationFrame(update);
            }

            function handleIntersect(entries) {
                for (var i = 0; i < entries.length; i++) {
                    if (entries[i].isIntersecting && !animated) {
                        animated = true;
                        for (var j = 0; j < counters.length; j++) {
                            animateCounter(counters[j]);
                        }
                        if (observer) observer.disconnect();
                        break;
                    }
                }
            }

            if ('IntersectionObserver' in window) {
                observer = new IntersectionObserver(handleIntersect, { threshold: 0.3 });
                for (var k = 0; k < counters.length; k++) {
                    observer.observe(counters[k]);
                }
            } else {
                // Fallback: animate immediately
                for (var m = 0; m < counters.length; m++) {
                    animateCounter(counters[m]);
                }
            }
        }

        /* ============================================================
           10. PERFORMANCE OPTIMIZATIONS
           ============================================================ */

        function initPerformanceOptimizations() {
            // Lazy load images
            var lazyImages = document.querySelectorAll('img[loading="lazy"]');

            if ('IntersectionObserver' in window) {
                var imageObserver = new IntersectionObserver(function(entries) {
                    for (var i = 0; i < entries.length; i++) {
                        if (entries[i].isIntersecting) {
                            var img = entries[i].target;
                            if (img.dataset.src) {
                                img.src = img.dataset.src;
                                img.removeAttribute('data-src');
                            }
                            imageObserver.unobserve(img);
                        }
                    }
                });

                for (var j = 0; j < lazyImages.length; j++) {
                    imageObserver.observe(lazyImages[j]);
                }
            }

            // Debounce resize events
            var resizeTimeout;
            window.addEventListener('resize', function() {
                clearTimeout(resizeTimeout);
                resizeTimeout = setTimeout(function() {
                    // Handle any resize-specific logic if needed
                }, 250);
            });
        }

        /* ============================================================
           11. ACCESSIBILITY ENHANCEMENTS
           ============================================================ */

        function initAccessibility() {
            // Add aria-current to active nav links
            var activeLinks = document.querySelectorAll('.nav-link.active');
            for (var i = 0; i < activeLinks.length; i++) {
                activeLinks[i].setAttribute('aria-current', 'page');
            }

            // Add aria-label to external links
            var externalLinks = document.querySelectorAll('a[target="_blank"]');
            for (var j = 0; j < externalLinks.length; j++) {
                if (!externalLinks[j].getAttribute('aria-label')) {
                    externalLinks[j].setAttribute('aria-label', 'Opens in new tab');
                }
            }
        }

        /* ============================================================
           12. INITIALIZE EVERYTHING
           ============================================================ */

        function init() {
            // Core features
            initMobileMenu();
            initSliders();
            initScrollReveal();
            initBackToTop();
            initSmoothScroll();
            initNavbarScroll();
            initFormValidation();
            initCounters();
            initPerformanceOptimizations();
            initAccessibility();

            console.log('✅ Elegant Events - All systems ready.');
        }

        // Start
        init();

    }); // end DOMContentLoaded

})();