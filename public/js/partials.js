// Function to load partials
async function loadPartials() {
    try {
        // Load header
        const headerResponse = await fetch('/partials/header.html');
        const headerHtml = await headerResponse.text();
        document.querySelector('header').outerHTML = headerHtml;

        // Load footer
        const footerResponse = await fetch('/partials/footer.html');
        const footerHtml = await footerResponse.text();
        document.querySelector('footer').outerHTML = footerHtml;

        // Update active menu item based on current page
        const currentPage = window.location.pathname.split('/').pop();
        const menuItems = document.querySelectorAll('.nav.menu li');
        menuItems.forEach(item => {
            const link = item.querySelector('a');
            if (link && link.getAttribute('href') === currentPage) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    } catch (error) {
        console.error('Error loading partials:', error);
    }
}

// Load partials when page loads
document.addEventListener('DOMContentLoaded', loadPartials); 