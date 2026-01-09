Feature: User Management
  As an Admin
  I want to manage users
  So that I can control access and organize users

  Background:
    Given I am logged in as an Admin

  @backend @frontend
  Scenario: List all users
    Given a customer "alice" exists
    And a customer "bob" exists
    When I list all users
    Then I should see user "alice" in the list
    And I should see user "bob" in the list

  @backend @frontend
  Scenario: View user details
    Given a customer "charlie" exists
    When I view user "charlie" details
    Then I should see the user has role "customer"
    And I should see the user has username "charlie"

  @backend @frontend
  Scenario: Promote user to Admin
    Given a customer "dave" exists
    When I update user "dave" role to "admin"
    Then user "dave" should have role "admin"

  @backend @frontend
  Scenario: Demote Admin to Customer
    Given an admin "eve" exists
    When I update user "eve" role to "customer"
    Then user "eve" should have role "customer"

  @backend @frontend
  Scenario: View user's group memberships
    Given a customer "frank" exists
    And a user group "testers" exists with description "Test users"
    And user "frank" is a member of group "testers"
    When I view user "frank" details
    Then I should see the user is in group "testers"

  @backend @frontend
  Scenario: User with no groups shows empty group list
    Given a customer "grace" exists
    When I view user "grace" details
    Then I should see the user has no groups

  @backend-only
  Scenario: Cannot list users as Customer
    Given I am logged in as a Customer
    When I try to list all users
    Then I should receive a "PermissionDeniedError"

  @backend-only
  Scenario: Cannot view user details as Customer
    Given a customer "henry" exists
    And I am logged in as a Customer
    When I try to view user "henry" details
    Then I should receive a "PermissionDeniedError"

  @backend-only
  Scenario: Cannot update user role as Customer
    Given a customer "ivan" exists
    And I am logged in as a Customer
    When I try to update user "ivan" role to "admin"
    Then I should receive a "PermissionDeniedError"

  @backend-only
  Scenario: Cannot view nonexistent user
    When I try to view nonexistent user details
    Then I should receive a "UserNotFoundError"

  @backend-only
  Scenario: Cannot update role of nonexistent user
    When I try to update nonexistent user role to "admin"
    Then I should receive a "UserNotFoundError"
