Feature: Delete Product
  As an Admin
  I want to delete products
  So that I can remove items from the catalog

  Background:
    Given I am logged in as an Admin
    And a product "Old Widget" exists with price "$10.00" and stock quantity 50

  Scenario: Successfully soft delete a product
    When I delete the product "Old Widget"
    Then the product "Old Widget" should be marked as deleted
    And the product "Old Widget" should not appear in the product catalog

  Scenario: Admin can see deleted products when including deleted
    When I delete the product "Old Widget"
    Then the product "Old Widget" should appear when including deleted products

  Scenario: Cannot delete product as Customer
    Given I am logged in as a Customer
    When I try to delete the product "Old Widget"
    Then I should receive a "PermissionDeniedError"

  Scenario: Cannot delete product that is in a cart
    Given I am logged in as a Customer
    And I add 2 "Old Widget" to my cart
    And I am logged in as an Admin
    When I try to delete the product "Old Widget"
    Then I should receive a "ProductInUseError"

  Scenario: Can restore a deleted product
    Given the product "Old Widget" has been deleted
    When I restore the product "Old Widget"
    Then the product "Old Widget" should appear in the product catalog
