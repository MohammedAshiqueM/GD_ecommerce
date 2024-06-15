// Query selectors
const icon = document.querySelector('.icon');
const search = document.querySelector('.search');
const searchInput = document.getElementById('mysearch');

// Mouse enter event handler for search
search.addEventListener('mouseenter', function() {
    search.classList.toggle('active');
});

// Mouse leave event handler for search
search.addEventListener('mouseleave', function() {
    if (!searchInput.value.trim()) {
        search.classList.remove('active');
    }
});

// Reset function
function reset() {
    searchInput.value = '';
    search.classList.remove('active');
}

// Function to handle input change
function handleInputChange() {
    if (searchInput.value.trim()) {
        search.classList.add('active');
    } else {
        search.classList.remove('active');
    }
}

// Add event listener for input change
searchInput.addEventListener('input', handleInputChange);

// Welcome message
let welcome;
const date = new Date();
const hour = date.getHours();
const minute = (date.getMinutes() < 10 ? '0' : '') + date.getMinutes();
const second = (date.getSeconds() < 10 ? '0' : '') + date.getSeconds();

if (hour < 12) {
    welcome = 'good morning';
} else if (hour < 17) {
    welcome = 'good afternoon';
} else {
    welcome = 'good evening';
}

// DOM ready event handler
document.addEventListener('DOMContentLoaded', function() {
    const body = document.querySelector('body');
    const toggled = document.getElementById('toggle');

    // Click event handler for toggle button
    toggled.addEventListener('click', function() {
        body.classList.toggle('light');
        toggled.classList.toggle('active');
    });

    // Mouse enter event handler for dashboard
    document.getElementById('dashboard').addEventListener('mouseenter', function() {
        this.innerHTML = welcome;
    });

    // Mouse leave event handler for dashboard
    document.getElementById('dashboard').addEventListener('mouseleave', function() {
        this.innerHTML = 'DASHBOARD';
    });

    // Mouse enter event handler for kleenpulse
    document.getElementById('kleenpulse').addEventListener('mouseenter', function() {
        this.innerHTML = 'welcome';
    });

    // Mouse leave event handler for kleenpulse
    document.getElementById('kleenpulse').addEventListener('mouseleave', function() {
        this.innerHTML = 'LiquidTime';
    });
});
