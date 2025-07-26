// Global variables
let isMobileMenuOpen = false;
let activeSection = 'home';

// Initialize the page
// document.addEventListener('DOMContentLoaded', function() {
//     // Initialize Lucide icons
//     lucide.createIcons();
    
//     // Setup event listeners
//     setupScrollHandlers();
//     setupIntersectionObserver();
//     setupFormHandler();
//     setupVideoHandler();
    
//     // Initial animations
//     animateOnLoad();
// });

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Lucide icons
    lucide.createIcons();
    
    // Setup event listeners
    setupScrollHandlers();
    setupIntersectionObserver();
    setupFormHandler();
    setupVideoHandler();
    setupPresentationHandler(); // <-- This is the new line you need to add
    
    // Initial animations
    animateOnLoad();
});

// Scroll handlers
function setupScrollHandlers() {
    let ticking = false;
    
    window.addEventListener('scroll', function() {
        if (!ticking) {
            requestAnimationFrame(function() {
                handleScroll();
                ticking = false;
            });
            ticking = true;
        }
    });
}

function handleScroll() {
    const header = document.getElementById('header');
    const scrollY = window.scrollY;
    
    // Header scroll effect
    if (scrollY > 50) {
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
    
    // Update active navigation
    updateActiveNavigation();
}

function updateActiveNavigation() {
    const sections = ['home', 'features', 'demo', 'about', 'contact'];
    const scrollY = window.scrollY;
    
    for (let i = sections.length - 1; i >= 0; i--) {
        const element = document.getElementById(sections[i]);
        if (element && scrollY >= element.offsetTop - 100) {
            if (activeSection !== sections[i]) {
                activeSection = sections[i];
                updateNavLinks();
            }
            break;
        }
    }
}

function updateNavLinks() {
    // Update desktop nav links
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        const section = link.getAttribute('data-section');
        if (section === activeSection) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
    
    // Update mobile nav links
    const mobileNavLinks = document.querySelectorAll('.mobile-nav-link');
    mobileNavLinks.forEach(link => {
        const section = link.getAttribute('data-section');
        if (section === activeSection) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// Smooth scroll to section
function scrollToSection(sectionId) {
    const element = document.getElementById(sectionId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Close mobile menu if open
    if (isMobileMenuOpen) {
        toggleMobileMenu();
    }
}

// Mobile menu toggle
function toggleMobileMenu() {
    const mobileMenu = document.querySelector('.mobile-menu');
    const menuIcon = document.querySelector('.menu-icon');
    const closeIcon = document.querySelector('.close-icon');
    
    isMobileMenuOpen = !isMobileMenuOpen;
    
    if (isMobileMenuOpen) {
        mobileMenu.classList.remove('hidden');
        menuIcon.classList.add('hidden');
        closeIcon.classList.remove('hidden');
    } else {
        mobileMenu.classList.add('hidden');
        menuIcon.classList.remove('hidden');
        closeIcon.classList.add('hidden');
    }
}

// Intersection Observer for animations
function setupIntersectionObserver() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries, observer) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const target = entry.target;

            // Trigger the separate flowchart animation function immediately
            if (target.classList.contains('flowchart-container')) {
                animateFlowchart();
            }

            // Handle elements with a staggered animation delay
            if (target.classList.contains('feature-card')) {
                const delay = parseInt(target.getAttribute('data-card') || '0') * 150;
                setTimeout(() => {
                    target.classList.add('visible');
                    observer.unobserve(target); // Unobserve AFTER the delay
                }, delay);
            } else if (target.classList.contains('team-member')) {
                const delay = parseInt(target.getAttribute('data-member') || '0') * 150;
                setTimeout(() => {
                    target.classList.add('visible');
                    observer.unobserve(target); // Unobserve AFTER the delay
                }, delay);
            } else if (target.classList.contains('demo-item')) {
                const delay = target === document.querySelector('.demo-item:first-child') ? 0 : 300;
                setTimeout(() => {
                    target.classList.add('visible');
                    observer.unobserve(target); // Unobserve AFTER the delay
                }, delay);
            } else {
                // Handle all other elements without a delay
                target.classList.add('visible');
                observer.unobserve(target); // Unobserve immediately
            }
        }
    });
}, observerOptions);
    
//     const observer = new IntersectionObserver(function(entries, observer) { // 1. Added 'observer' here
//     entries.forEach(entry => {
//         if (entry.isIntersecting) {
//             entry.target.classList.add('visible');
            
//             // Special handling for flowchart animation
//             if (entry.target.classList.contains('flowchart-container')) {
//                 animateFlowchart();
//             }
            
//             // Special handling for feature cards
//             if (entry.target.classList.contains('feature-card')) {
//                 const delay = parseInt(entry.target.getAttribute('data-card')) * 150;
//                 setTimeout(() => {
//                     entry.target.classList.add('visible');
//                 }, delay);
//             }
            
//             // Special handling for team members
//             if (entry.target.classList.contains('team-member')) {
//                 const delay = parseInt(entry.target.getAttribute('data-member')) * 150;
//                 setTimeout(() => {
//                     entry.target.classList.add('visible');
//                 }, delay);
//             }
            
//             // Special handling for demo items
//             if (entry.target.classList.contains('demo-item')) {
//                 const delay = entry.target === document.querySelector('.demo-item:first-child') ? 0 : 300;
//                 setTimeout(() => {
//                     entry.target.classList.add('visible');
//                 }, delay);
//             }
            
//             // 2. Add this line to stop observing the element
//             observer.unobserve(entry.target);
//         }
//     });
// }, observerOptions);
    
    // Observe elements
    const elementsToObserve = [
        '.section-header',
        '.flowchart-container',
        '.feature-card',
        '.demo-item',
        '.team-member',
        '.team-stats'
    ];
    
    elementsToObserve.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => observer.observe(element));
    });
}

// Animate flowchart
function animateFlowchart() {
    const steps = document.querySelectorAll('.flow-step');
    const arrows = document.querySelectorAll('.flow-arrow');
    
    steps.forEach((step, index) => {
        setTimeout(() => {
            step.classList.add('visible');
        }, index * 200);
    });
    
    arrows.forEach((arrow, index) => {
        setTimeout(() => {
            arrow.classList.add('visible');
        }, (index + 1) * 200);
    });
}

// Initial load animations
function animateOnLoad() {
    // Animate hero elements
    setTimeout(() => {
        const heroCard = document.querySelector('.hero-card');
        if (heroCard) {
            heroCard.style.opacity = '1';
            heroCard.style.transform = 'scale(1)';
        }
    }, 500);
}

// Form handler
// function setupFormHandler() {
//     const form = document.getElementById('contact-form');
//     const submitBtn = document.getElementById('submit-btn');
    
//     form.addEventListener('submit', async function(e) {
//         e.preventDefault();
        
//         // Get form elements
//         const submitIcon = submitBtn.querySelector('.submit-icon');
//         const submitText = submitBtn.querySelector('.submit-text');
//         const submitSpinner = submitBtn.querySelector('.submit-spinner');
//         const submitSuccess = submitBtn.querySelector('.submit-success');
        
//         // Show loading state
//         submitBtn.disabled = true;
//         submitIcon.classList.add('hidden');
//         submitText.classList.add('hidden');
//         submitSpinner.classList.remove('hidden');
        
//         // Simulate form submission
//         await new Promise(resolve => setTimeout(resolve, 1500));
        
//         // Show success state
//         submitSpinner.classList.add('hidden');
//         submitSuccess.classList.remove('hidden');
//         submitBtn.style.background = '#22c55e';
        
//         // Reset form
//         form.reset();
        
//         // Reset button after 3 seconds
//         setTimeout(() => {
//             submitBtn.disabled = false;
//             submitSuccess.classList.add('hidden');
//             submitIcon.classList.remove('hidden');
//             submitText.classList.remove('hidden');
//             submitBtn.style.background = '';
//         }, 3000);
//     });
// }

function setupFormHandler() {
    const form = document.getElementById('contact-form');
    if (!form) return;

    // PASTE YOUR 3 KEYS FROM EMAILJS HERE
    const publicKey = 'Gek_oA23TXvZIGTPj';
    const serviceID = 'service_4idhiqq';
    const templateID = 'template_55e83i4';

    // This initializes EmailJS with your account's public key
    emailjs.init({ publicKey: publicKey });

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const submitBtn = document.getElementById('submit-btn');
        const submitIcon = submitBtn.querySelector('.submit-icon');
        const submitText = submitBtn.querySelector('.submit-text');
        const submitSpinner = submitBtn.querySelector('.submit-spinner');
        const submitSuccess = submitBtn.querySelector('.submit-success');
        
        // Show the loading spinner on the button
        submitBtn.disabled = true;
        submitIcon.classList.add('hidden');
        submitText.classList.add('hidden');
        submitSpinner.classList.remove('hidden');

        // This is the line that actually sends the form data as an email
        emailjs.sendForm(serviceID, templateID, this)
            .then(() => {
                // If the email sends successfully, show the success message
                submitSpinner.classList.add('hidden');
                submitSuccess.classList.remove('hidden');
                submitBtn.style.background = '#22c55e';
                form.reset();
            }, (error) => {
                // If there's an error, show an alert
                alert('Failed to send message. Please try again.');
                console.error('EMAILJS FAILED...', error);
                submitSpinner.classList.add('hidden');
                submitIcon.classList.remove('hidden');
                submitText.classList.remove('hidden');
            })
            .finally(() => {
                // After 3 seconds, reset the button back to normal
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitSuccess.classList.add('hidden');
                    submitIcon.classList.remove('hidden');
                    submitText.classList.remove('hidden');
                    submitBtn.style.background = '';
                }, 3000);
            });
    });
}

// Video handler
function setupVideoHandler() {
    const videoPlaceholder = document.getElementById('video-placeholder');
    const videoIframe = document.getElementById('demo-video');
    
    if (videoPlaceholder && videoIframe) {
        videoPlaceholder.addEventListener('click', function() {
            // Load the actual video
            videoIframe.src = 'https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1';
            
            // Hide placeholder and show video
            videoPlaceholder.classList.add('hidden');
            videoIframe.classList.remove('hidden');
        });
    }
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Handle window resize
window.addEventListener('resize', debounce(function() {
    // Close mobile menu on resize to desktop
    if (window.innerWidth > 768 && isMobileMenuOpen) {
        toggleMobileMenu();
    }
}, 250));

// Keyboard navigation support
document.addEventListener('keydown', function(e) {
    // Close mobile menu with Escape key
    if (e.key === 'Escape' && isMobileMenuOpen) {
        toggleMobileMenu();
    }
    
    // Navigate sections with arrow keys (when focused on nav)
    if (document.activeElement.classList.contains('nav-link') || 
        document.activeElement.classList.contains('mobile-nav-link')) {
        
        const sections = ['home', 'features', 'demo', 'about', 'contact'];
        const currentIndex = sections.indexOf(activeSection);
        
        if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
            e.preventDefault();
            const nextIndex = (currentIndex + 1) % sections.length;
            scrollToSection(sections[nextIndex]);
        } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
            e.preventDefault();
            const prevIndex = (currentIndex - 1 + sections.length) % sections.length;
            scrollToSection(sections[prevIndex]);
        }
    }
});

// Smooth scroll polyfill for older browsers
if (!('scrollBehavior' in document.documentElement.style)) {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/gh/iamdustan/smoothscroll@master/src/smoothscroll.js';
    document.head.appendChild(script);
}

// Performance optimization: Reduce motion for users who prefer it
if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.documentElement.style.setProperty('--animation-duration', '0.01ms');
    document.documentElement.style.setProperty('--transition-duration', '0.01ms');
}

// Add focus visible polyfill for better keyboard navigation
document.addEventListener('keydown', function(e) {
    if (e.key === 'Tab') {
        document.body.classList.add('keyboard-navigation');
    }
});

document.addEventListener('mousedown', function() {
    document.body.classList.remove('keyboard-navigation');
});

// Lazy loading for images
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            }
        });
    });
    
    document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
    });
}

function setupPresentationHandler() {
    const pptButton = document.getElementById('open-ppt-btn');
    const pptIframe = document.querySelector('.presentation-iframe');

    if (pptButton && pptIframe) {
        pptButton.addEventListener('click', function() {
            const pptSrc = pptIframe.src;
            window.open(pptSrc, '_blank');
        });
    }
}