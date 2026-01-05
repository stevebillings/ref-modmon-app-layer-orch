# Project requirements

A minimal e-commerce web application demonstrating cross-aggregate operations. When a user adds an item to their cart, stock must be reserved (Product aggregate) and the cart updated (Cart aggregate). When the cart is submitted, an immutable Order is created.

## Functional requirements

### Aggregates

- **Product**: Represents an item for sale with available stock
- **Cart**: The user's shopping cart (one cart per user)
- **Order**: A submitted, immutable record of a purchase (associated with the user who placed it), including a verified shipping address

### Cross-Aggregate Operations

| Action | Aggregates Affected |
|--------|---------------------|
| Add item to cart | Cart (add/update item), Product (reserve stock) |
| Remove item from cart | Cart (remove item), Product (release stock) |
| Submit cart | Cart (clear), Order (create from cart contents) |

### Pages

1. **Login Page**
   - Username and password form
   - Redirect to landing page on successful login
   - Default admin credentials displayed for demo purposes

2. **Landing Page**
   - Navigation to Product Catalog, Cart, and Order History pages
   - Display current cart item count (for logged-in users)
   - Show login/logout status and username
   - Protected actions require login

3. **Product Catalog Page**
   - View all products showing name, price, and available stock (public)
   - Create new products - admin only (name, price, initial stock quantity)
   - Delete products - admin only (only if not in cart and not referenced in any order)
   - Add to Cart button for each product (specify quantity) — requires login, reserves stock immediately
   - Cannot add more than available stock

4. **Cart Page** (requires login)
   - View current user's cart with items, quantities, unit prices, subtotals, and total
   - Remove items from cart — releases reserved stock
   - Adjust item quantity — adjusts stock reservation accordingly
   - **Shipping address form** — street, city, state, postal code, country
   - Submit Order button — verifies shipping address, creates an immutable Order, and clears the cart
   - Cannot increase quantity beyond available stock
   - Cannot submit an empty cart
   - Cannot submit without a valid shipping address

5. **Order History Page** (requires login)
   - Admins see all orders; customers see only their own orders
   - View submitted orders showing date, items, quantities, prices, and total
   - Orders are immutable and cannot be deleted

### Roles and Permissions

- **Admin**: Can create/delete products, view all orders
- **Customer**: Can manage their own cart, view their own orders

## Non Functional requirements

- Backend: Python/Django
- Frontend: Typescript/React
- Keep this as simple as possible while meeting all requirements in this spec.
- We only need to run in dev mode on localhost.
- Multi-user application with Django session-based authentication.
- Two roles: Admin and Customer (admin creates user accounts).
- Products are immutable once created (only stock quantity changes via cart operations). Orders are immutable once submitted.
- Cart items can be added, removed, or have quantity adjusted.
- Delete operations require confirmation dialogs.

## Currency Format

- **Display**: Always show dollar sign and two decimal places (e.g., "$12.99", "$5.00")
- **Entry**: Accept numeric input; frontend formats for display

## Empty States

- No products: "No products available. Add products to the catalog to get started."
- Empty cart: "Your cart is empty. Browse the product catalog to add items."
- No orders: "No orders yet. Submit your cart to create your first order."

