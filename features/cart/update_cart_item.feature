Feature: Update Cart Item Quantity
  As a Customer
  I want to change item quantities in my cart
  So that I can adjust my purchase before checkout

  Background:
    Given I am logged in as a Customer
    And a product "Headphones" exists with price "$149.99" and stock quantity 20
    And my cart contains 5 "Headphones"

  @backend @frontend
  Scenario: Increase item quantity
    When I update "Headphones" quantity to 8
    Then my cart should contain 8 "Headphones"

  @backend-only
  Scenario: Increasing quantity reserves more stock
    When I update "Headphones" quantity to 8
    Then the product "Headphones" should have stock quantity 12

  @backend @frontend
  Scenario: Decrease item quantity
    When I update "Headphones" quantity to 2
    Then my cart should contain 2 "Headphones"

  @backend-only
  Scenario: Decrease item quantity releases stock
    When I update "Headphones" quantity to 2
    Then the product "Headphones" should have stock quantity 18

  @backend-only
  Scenario: Cannot increase beyond available stock
    When I try to update "Headphones" quantity to 25
    Then I should receive an "InsufficientStockError"
    And my cart should contain 5 "Headphones"

  @backend-only
  Scenario: Cannot update to zero quantity
    When I try to update "Headphones" quantity to 0
    Then I should receive a "ValidationError"

  @backend-only
  Scenario: Cannot update nonexistent cart item
    When I try to update "Nonexistent Item" quantity to 5
    Then I should receive a "CartItemNotFoundError"
