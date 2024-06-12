function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', function() {
    const customerOptions = document.querySelectorAll('.customer-dropdown-options');

    customerOptions.forEach(button => {
        const currentCustomerElement = document.getElementById('current-customer');
        const currentCustomerInitials = document.getElementById('current-customer-initials');

        button.addEventListener('click', (event) => {
            const customerId = event.target.dataset.customerId;
            const customerInitials = event.target.dataset.customerInitials;

            currentCustomerElement.dataset.customerId = customerId;
            currentCustomerInitials.textContent = customerInitials;

            const csrftoken = getCookie('csrftoken');
            fetch('/api/current_customer', {
                method: 'POST',
                body: JSON.stringify({ current_customer_id: customerId }),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                }
            })
            .then(response => {
                if (response.ok) {
                    window.location.href = '/';
                } else {
                    console.error('request failed:', response);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });

        button.addEventListener('touchstart', (event) => {
            const customerId = event.target.dataset.customerId;
            const customerInitials = event.target.dataset.customerInitials;

            currentCustomerElement.dataset.customerId = customerId;
            currentCustomerInitials.textContent = customerInitials;
        });
    });

    document.getElementById('logout-link').addEventListener('click', function(event) {
        event.preventDefault();  // Prevent the default link behavior
        const csrftoken = getCookie('csrftoken');

        fetch('/logout/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken

            }
        })
        .then(response => {
            if (response.ok) {
                window.location.href = '/';
            } else {
                console.error('Logout failed:', response);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
});
