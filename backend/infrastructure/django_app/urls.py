from django.urls import path

from infrastructure.django_app import auth_views, views

urlpatterns = [
    # Auth endpoints
    path("auth/login/", auth_views.login_view, name="auth-login"),
    path("auth/logout/", auth_views.logout_view, name="auth-logout"),
    path("auth/session/", auth_views.session_view, name="auth-session"),
    # Product endpoints
    path("products/", views.products_list, name="products-list"),
    path("products/create/", views.product_create, name="product-create"),
    path("products/report/", views.product_report, name="product-report"),
    path("products/<str:product_id>/", views.product_delete, name="product-delete"),
    path(
        "products/<str:product_id>/restore/",
        views.product_restore,
        name="product-restore",
    ),
    # Cart endpoints
    path("cart/", views.cart_get, name="cart-get"),
    path("cart/items/", views.cart_add_item, name="cart-add-item"),
    path(
        "cart/items/<str:product_id>/",
        views.cart_update_item,
        name="cart-update-item",
    ),
    path(
        "cart/items/<str:product_id>/remove/",
        views.cart_remove_item,
        name="cart-remove-item",
    ),
    path("cart/verify-address/", views.cart_verify_address, name="cart-verify-address"),
    path("cart/submit/", views.cart_submit, name="cart-submit"),
    # Order endpoints
    path("orders/", views.orders_list, name="orders-list"),
    # Feature flag admin endpoints
    path("admin/feature-flags/", views.feature_flags_list, name="feature-flags-list"),
    path(
        "admin/feature-flags/create/",
        views.feature_flag_create,
        name="feature-flag-create",
    ),
    path(
        "admin/feature-flags/<str:flag_name>/",
        views.feature_flag_detail,
        name="feature-flag-detail",
    ),
    # Debug/test endpoints
    path("debug/trigger-error/", views.trigger_test_error, name="trigger-test-error"),
    # Health check and metrics
    path("health/", views.health_check, name="health-check"),
    path("metrics/", views.metrics, name="metrics"),
]
