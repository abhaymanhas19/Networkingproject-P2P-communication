from .models import CustomerUsers
from .utils import get_customer_routers


def dashboard_context(request):


    user = request.user

    if not user.is_authenticated:
        return {}

    customer_id = None
    customer_users = CustomerUsers.objects.filter(user=user).select_related('customer')
    customers = [cu.customer for cu in customer_users]
    current_customer = {}
    context ={}
    context["current_customer"] = {}
    if 'current_customer' in request.session:
        current_customer = request.session['current_customer']
        context["current_customer"] = current_customer
    else:
        if customers:
            context["current_customer"] = customers[0].basic_info
            request.session['current_customer'] = customers[0].basic_info
            current_customer = request.session['current_customer']

    customer_id = int(current_customer.get("id", 0))
    all_routers = get_customer_routers(customer_id)
    context["customer_routers"] = all_routers
    context["customer_data"] = customers
    context["user_info"] = user
    return context
