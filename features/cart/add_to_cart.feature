Feature: Add Item to Cart
  As a Customer
  I want to add products to my cart
  So that I can purchase them later

  Background:
    Given I am logged in as a Customer
    And a product "Laptop" exists with price "$999.99" and stock quantity 10

  @backend @frontend
  Scenario: Successfully add item to cart
    When I add 2 "Laptop" to my cart
    Then my cart should contain 2 "Laptop" at "$999.99" each

  @backend-only
  Scenario: Adding to cart reserves stock
    When I add 2 "Laptop" to my cart
    Then the product "Laptop" should have stock quantity 8

  @backend @frontend
  Scenario: Add same product twice merges quantities
    Given my cart contains 2 "Laptop"
    When I add 3 "Laptop" to my cart
    Then my cart should contain 5 "Laptop"

  @backend-only
  Scenario: Adding more merges quantities and reserves additional stock
    Given my cart contains 2 "Laptop"
    When I add 3 "Laptop" to my cart
    Then the product "Laptop" should have stock quantity 5

  @backend-only
  Scenario: Cannot add more than available stock
    When I try to add 15 "Laptop" to my cart
    Then I should receive an "InsufficientStockError"
    And my cart should be empty
    And the product "Laptop" should have stock quantity 10

  @backend-only
  Scenario: Cart item snapshots product price
    Given I add 1 "Laptop" to my cart
    When the product "Laptop" price changes to "$1099.99"
    Then my cart item "Laptop" should still show "$999.99" per unit

  @backend-only
  Scenario: Cannot add zero quantity
    When I try to add 0 "Laptop" to my cart
    Then I should receive a "ValidationError"

  @backend-only
  Scenario: Cannot add nonexistent product
    When I try to add 1 "Nonexistent Product" to my cart
    Then I should receive a "ProductNotFoundError"
