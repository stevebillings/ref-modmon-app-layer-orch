Feature: Create Product
  As an Admin
  I want to create new products
  So that customers can purchase them

  Background:
    Given I am logged in as an Admin

  @backend @frontend
  Scenario: Successfully create a product
    When I create a product with name "Widget Pro" price "$29.99" and stock quantity 100
    Then the product "Widget Pro" should exist
    And the product "Widget Pro" should have price "$29.99"
    And the product "Widget Pro" should have stock quantity 100

  @backend-only
  Scenario: Cannot create product with duplicate name
    Given a product "Widget Pro" exists with price "$19.99" and stock quantity 50
    When I try to create a product with name "Widget Pro" price "$29.99" and stock quantity 100
    Then I should receive a "DuplicateProductError"

  @backend-only
  Scenario: Cannot create product as Customer
    Given I am logged in as a Customer
    When I try to create a product with name "Widget Pro" price "$29.99" and stock quantity 100
    Then I should receive a "PermissionDeniedError"

  @backend-only
  Scenario: Cannot create product with empty name
    When I try to create a product with name "" price "$29.99" and stock quantity 100
    Then I should receive a "ValidationError"

  @backend-only
  Scenario: Cannot create product with negative price
    When I try to create a product with name "Widget Pro" price "$-5.00" and stock quantity 100
    Then I should receive a "ValidationError"

  @backend-only
  Scenario: Cannot create product with negative stock
    When I try to create a product with name "Widget Pro" price "$29.99" and stock quantity -10
    Then I should receive a "ValidationError"
