Feature: View Orders
  As a user
  I want to view order history
  So that I can see my past purchases

  @backend @frontend
  Scenario: Customer sees only their own orders
    Given a customer "alice" has submitted an order for "Widget" at "$19.99" quantity 2
    And a customer "bob" has submitted an order for "Gadget" at "$29.99" quantity 1
    When I am logged in as customer "alice"
    And I view my orders
    Then I should see 1 order
    And the order should contain "Widget" quantity 2

  @backend @frontend
  Scenario: Admin sees all orders
    Given a customer "alice" has submitted an order for "Widget" at "$19.99" quantity 2
    And a customer "bob" has submitted an order for "Gadget" at "$29.99" quantity 1
    When I am logged in as an Admin
    And I view all orders
    Then I should see 2 orders

  @backend-only
  Scenario: Orders are immutable
    Given a customer "alice" has submitted an order for "Widget" at "$19.99" quantity 2
    When the product "Widget" price changes to "$24.99"
    And I am logged in as customer "alice"
    And I view my orders
    Then the order should contain "Widget" at "$19.99" each

  @backend @frontend
  Scenario: No orders shows empty list
    Given I am logged in as a Customer
    And I have no previous orders
    When I view my orders
    Then I should see 0 orders
