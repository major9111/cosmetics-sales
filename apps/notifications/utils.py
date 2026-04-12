
"""Notification utilities - create in-app + optional email alerts."""

def notify_user(user, title, message, ntype="general"):
    """Create an in-app notification for a user."""
    try:
        from .models import Notification
        Notification.objects.create(user=user, title=title, message=message, type=ntype)
    except Exception:
        pass


def notify_managers(branch, title, message, ntype="general"):
    """Notify all managers and super admins about something."""
    from apps.accounts.models import User
    managers = User.objects.filter(
        is_active=True,
        role__in=["super_admin", "branch_manager"]
    )
    if branch:
        managers = managers.filter(branch=branch) | User.objects.filter(role="super_admin")
    for user in managers.distinct():
        notify_user(user, title, message, ntype)


def send_low_stock_alerts():
    """Check all stock and notify managers of items below reorder level."""
    from apps.stock.models import Stock
    from apps.products.models import Product
    low_items = []
    for stock in Stock.objects.select_related("product", "branch").filter(product__is_active=True):
        reorder = getattr(stock.product, "reorder_level", 10)
        if stock.quantity <= reorder:
            low_items.append(stock)
            notify_managers(
                stock.branch,
                f"Low Stock: {stock.product.name}",
                f"{stock.product.name} at {stock.branch.name} has only {stock.quantity} units left (reorder level: {reorder}).",
                ntype="low_stock"
            )
    return len(low_items)


def send_expiry_alerts():
    """Notify managers of products expiring within 30 days."""
    from apps.products.models import Product
    from datetime import date, timedelta
    today = date.today()
    soon  = today + timedelta(days=30)
    products = Product.objects.filter(is_active=True, expiry_date__isnull=False, expiry_date__lte=soon)
    for p in products:
        status = "EXPIRED" if p.expiry_date < today else f"expires {p.expiry_date}"
        notify_managers(
            None,
            f"Expiry Alert: {p.name}",
            f"{p.name} ({status}). Please remove or discount immediately.",
            ntype="expiry"
        )
    return products.count()
