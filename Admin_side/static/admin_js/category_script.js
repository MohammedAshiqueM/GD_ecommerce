function blockCategory(categoryId) {
    fetch(`/administration/blockCategory/${categoryId}/`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (response.ok) {
            location.reload();
        } else {
            console.error('Failed to block category');
        }
    })
    .catch(error => {
        console.error('Error blocking category:', error);
    });
}

function unblockCategory(categoryId) {
    fetch(`/administration/unblockCategory/${categoryId}/`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (response.ok) {
            location.reload();
        } else {
            console.error('Failed to unblock category');
        }
    })
    .catch(error => {
        console.error('Error unblocking category:', error);
    });
}

function blockSubcategory(subcategoryId) {
    fetch(`/administration/blockSubcategory/${subcategoryId}/`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (response.ok) {
            location.reload();
        } else {
            console.error('Failed to block subcategory');
        }
    })
    .catch(error => {
        console.error('Error blocking subcategory:', error);
    });
}

function unblockSubcategory(productId) {
    fetch(`/administration/unblockSubcategory/${productId}/`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (response.ok) {
            location.reload();
        } else {
            console.error('Failed to unblock subcategory');
        }
    })
    .catch(error => {
        console.error('Error unblocking subcategory:', error);
    });
}

function blockproduct(productId) {
    fetch(`/administration/blockProduct/${productId}/`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (response.ok) {
            location.reload();
        } else {
            console.error('Failed to block subcategory');
        }
    })
    .catch(error => {
        console.error('Error blocking subcategory:', error);
    });
}

function unblockproduct(subcategoryId) {
    fetch(`/administration/unblockProduct/${subcategoryId}/`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (response.ok) {
            location.reload();
        } else {
            console.error('Failed to unblock subcategory');
        }
    })
    .catch(error => {
        console.error('Error unblocking subcategory:', error);
    });
}

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
