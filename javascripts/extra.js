// Custom JavaScript for AWS Cloud Utilities documentation

document.addEventListener('DOMContentLoaded', function() {
    // Add copy functionality to command examples
    const codeBlocks = document.querySelectorAll('pre code');
    codeBlocks.forEach(function(block) {
        if (block.textContent.startsWith('aws-cloud-utilities')) {
            block.classList.add('command-example');
        }
    });

    // Add smooth scrolling to anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
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

    // Enhance table responsiveness
    const tables = document.querySelectorAll('.md-typeset table');
    tables.forEach(function(table) {
        if (!table.parentElement.classList.contains('md-typeset__scrollwrap')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'md-typeset__scrollwrap';
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
    });

    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('.md-search__input');
            if (searchInput) {
                searchInput.focus();
            }
        }
    });

    // Add version info to footer if available
    const footer = document.querySelector('.md-footer');
    if (footer && !footer.querySelector('.version-info')) {
        const versionInfo = document.createElement('div');
        versionInfo.className = 'version-info';
        versionInfo.style.textAlign = 'center';
        versionInfo.style.padding = '1rem';
        versionInfo.style.fontSize = '0.8rem';
        versionInfo.style.opacity = '0.7';
        versionInfo.innerHTML = 'AWS Cloud Utilities v2 - Built with ❤️ for AWS operations';
        footer.appendChild(versionInfo);
    }
});

// Add analytics or tracking if needed (placeholder)
function trackPageView(page) {
    // Placeholder for analytics tracking
    console.log('Page view:', page);
}

// Track navigation
if (typeof window !== 'undefined') {
    window.addEventListener('load', function() {
        trackPageView(window.location.pathname);
    });
}
