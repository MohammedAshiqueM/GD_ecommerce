function blockUser(userId) {
    fetch(`/administration/block/${userId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
        .then(response => {
            if (response.ok) {
                // Update UI or do something after successful blocking
                location.reload();
            } else {
                console.error('Failed to block user');
            }
        })
        .catch(error => {
            console.error('Error blocking user:', error);
        });
}

function unblockUser(userId) {
    fetch(`/administration/unblock/${userId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
        .then(response => {
            if (response.ok) {
                // Update UI or do something after successful unblocking
                location.reload();
            } else {
                console.error('Failed to unblock user');
            }
        })
        .catch(error => {
            console.error('Error unblocking user:', error);
        });
}

// Function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
