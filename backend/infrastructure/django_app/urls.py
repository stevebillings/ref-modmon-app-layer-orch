from django.urls import path

from infrastructure.django_app import views

urlpatterns = [
    # Product endpoints
    path("products/", views.products_list_create, name="products-list-create"),
    path("products/<str:product_id>/", views.product_delete, name="product-delete"),

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
    path("cart/submit/", views.cart_submit, name="cart-submit"),

    # Order endpoints
    path("orders/", views.orders_list, name="orders-list"),
]
