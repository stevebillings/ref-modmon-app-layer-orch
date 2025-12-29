# Project requirements

A minimal e-commerce web application demonstrating cross-aggregate operations. When a user adds an item to their cart, stock must be reserved (Product aggregate) and the cart updated (Cart aggregate). When the cart is submitted, an immutable Order is created.

## Functional requirements

### Aggregates

- **Product**: Represents an item for sale with available stock
- **Cart**: The user's current shopping cart (single cart for single user)
- **Order**: A submitted, immutable record of a purchase

### Cross-Aggregate Operations

| Action | Aggregates Affected |
|--------|---------------------|
| Add item to cart | Cart (add/update item), Product (reserve stock) |
| Remove item from cart | Cart (remove item), Product (release stock) |
| Submit cart | Cart (clear), Order (create from cart contents) |

### Pages

1. **Landing Page**
   - Navigation to Product Catalog, Cart, and Order History pages
   - Display current cart item count

2. **Product Catalog Page**
   - View all products showing name, price, and available stock
   - Create new products (name, price, initial stock quantity)
   - Delete products (only if not in cart and not referenced in any order)

3. **Cart Page**
   - View current cart with items, quantities, unit prices, subtotals, and total
   - Add items to cart (select product, specify quantity) — reserves stock immediately
   - Remove items from cart — releases reserved stock
   - Adjust item quantity — adjusts stock reservation accordingly
   - Submit Order button — creates an immutable Order and clears the cart
   - Cannot add or increase quantity beyond available stock
   - Cannot submit an empty cart

4. **Order History Page**
   - View all submitted orders showing date, items, quantities, prices, and total
   - Orders are immutable and cannot be deleted

## Non Functional requirements

- Backend: Python/Django
- Frontend: Typescript/React
- Keep this as simple as possible while meeting all requirements in this spec.
- We only need to run in dev mode on localhost.
- Single-user application with no authentication required.
- Cart items can be added, removed, or have quantity adjusted. Orders are immutable once submitted.
- Delete operations require confirmation dialogs.

## Empty States

- No products: "No products available. Add products to the catalog to get started."
- Empty cart: "Your cart is empty. Browse the product catalog to add items."
- No orders: "No orders yet. Submit your cart to create your first order."

