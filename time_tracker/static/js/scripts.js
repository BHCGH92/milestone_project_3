// Save scroll position to allow for better UX, used on table pagniation clicks
document.addEventListener('DOMContentLoaded', function() {
    if ('scrollRestoration' in history) {
        history.scrollRestoration = 'manual';
    }
    const savedScroll = sessionStorage.getItem('scrollPos');
    
    if (savedScroll) {
        setTimeout(() => {
            window.scrollTo(0, parseInt(savedScroll));
            sessionStorage.removeItem('scrollPos');
        }, 10); 
    }
    function saveScrollPosition() {
        sessionStorage.setItem('scrollPos', window.scrollY);
    }
    document.querySelectorAll('.pagination a').forEach(link => {
        link.addEventListener('mousedown', saveScrollPosition);
        window.addEventListener('beforeunload', saveScrollPosition); 
    });
});