from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('branches/', include('apps.branches.urls')),
    path('products/', include('apps.products.urls')),
    path('stock/', include('apps.stock.urls')),
    path('sales/', include('apps.sales.urls')),
    path('ai/', include('apps.ai_scanner.urls')),
    path('dashboard/', include('apps.branches.dashboard_urls')),
    path('suppliers/', include('apps.suppliers.urls')),
    path('expenses/', include('apps.expenses.urls')),
    path('attendance/', include('apps.attendance.urls')),
    path('activity/', include('apps.activity_log.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('api/products/', include('apps.products.api_urls')),
    path('api/stock/', include('apps.stock.api_urls')),
    path('api/sales/', include('apps.sales.api_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
