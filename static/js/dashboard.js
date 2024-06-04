document.addEventListener('DOMContentLoaded', function() {

    const customerOptions = document.querySelectorAll('.customer-dropdown-options');
    const selectedCustomer =
    customerOptions.forEach(button => {
        const currentCustomerElement = document.getElementById('current-customer');
        const currentCustomerInitials = document.getElementById('current-customer-initials');

        button.addEventListener('click', (event) => {
            customerId = event.target.dataset.customerId;
            customerInitials = event.target.dataset.customerInitials;

            currentCustomerElement.dataset.customerId = customerId;
            currentCustomerInitials.textContent = customerInitials


        });

        button.addEventListener('touchstart', (event) => {
            customerId = event.target.dataset.customerId;
            customerInitials = event.target.dataset.customerInitials;

            currentCustomerElement.dataset.customerId = customerId;
            currentCustomerInitials.textContent = customerInitials

        });
    });

    document.getElementById('logout-link').addEventListener('click', function(event) {
        event.preventDefault();  // Prevent the default link behavior
        const csrftoken = getCookie('csrftoken');

        fetch('/logout/', {
            method: 'POST',
            headers: {
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
});
