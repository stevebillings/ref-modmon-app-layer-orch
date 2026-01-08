Feature: Remove Item from Cart
  As a Customer
  I want to remove items from my cart
  So that I can change my mind about purchases

  Background:
    Given I am logged in as a Customer
    And a product "Keyboard" exists with price "$79.99" and stock quantity 30
    And my cart contains 5 "Keyboard"

  @backend @frontend
  Scenario: Successfully remove item from cart
    When I remove "Keyboard" from my cart
    Then my cart should be empty

  @backend-only
  Scenario: Remove releases reserved stock
    When I remove "Keyboard" from my cart
    Then the product "Keyboard" should have stock quantity 30

  @backend-only
  Scenario: Cannot remove nonexistent cart item
    When I try to remove "Nonexistent Item" from my cart
    Then I should receive a "CartItemNotFoundError"
