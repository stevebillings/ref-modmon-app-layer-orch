Feature: Submit Cart
  As a Customer
  I want to submit my cart
  So that I can complete my purchase

  Background:
    Given I am logged in as a Customer
    And a product "Monitor" exists with price "$299.99" and stock quantity 15
    And my cart contains 2 "Monitor"

  Scenario: Successfully submit cart with verified address
    Given I have a valid shipping address:
      | street_line_1 | city     | state | postal_code | country |
      | 123 Main St   | Portland | OR    | 97201       | US      |
    When I submit my cart
    Then an order should be created with 1 item totaling "$599.98"
    And my cart should be empty
    And the order should have a verified shipping address

  Scenario: Order preserves item details as snapshots
    Given I have a valid shipping address:
      | street_line_1 | city     | state | postal_code | country |
      | 123 Main St   | Portland | OR    | 97201       | US      |
    When I submit my cart
    Then the order should contain "Monitor" at "$299.99" each

  Scenario: Cannot submit empty cart
    Given my cart is empty
    And I have a valid shipping address:
      | street_line_1 | city     | state | postal_code | country |
      | 123 Main St   | Portland | OR    | 97201       | US      |
    When I try to submit my cart
    Then I should receive an "EmptyCartError"

  Scenario: Cannot submit with invalid address
    Given I have an invalid shipping address:
      | street_line_1          | city    | state | postal_code | country |
      | Invalid Street Address | Nowhere | XX    | 00000       | US      |
    When I try to submit my cart
    Then I should receive an "AddressVerificationError"

  Scenario: Stock remains decremented after order
    Given I have a valid shipping address:
      | street_line_1 | city     | state | postal_code | country |
      | 123 Main St   | Portland | OR    | 97201       | US      |
    When I submit my cart
    Then the product "Monitor" should have stock quantity 13
