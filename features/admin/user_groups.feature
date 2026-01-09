Feature: User Groups
  As an Admin
  I want to manage user groups
  So that I can organize users for feature flag targeting

  Background:
    Given I am logged in as an Admin

  @backend @frontend
  Scenario: Successfully create a user group
    When I create a user group "beta_testers" with description "Users testing beta features"
    Then the user group "beta_testers" should exist
    And the user group "beta_testers" should have description "Users testing beta features"

  @backend @frontend
  Scenario: Delete a user group
    Given a user group "temporary_group" exists with description "Temporary"
    When I delete the user group "temporary_group"
    Then the user group "temporary_group" should not exist

  @backend @frontend
  Scenario: Add user to a group
    Given a user group "internal_users" exists with description "Internal team"
    And a customer "alice" exists
    When I add user "alice" to the group "internal_users"
    Then user "alice" should be a member of group "internal_users"

  @backend @frontend
  Scenario: Remove user from a group
    Given a user group "trial_users" exists with description "Trial users"
    And a customer "bob" exists
    And user "bob" is a member of group "trial_users"
    When I remove user "bob" from the group "trial_users"
    Then user "bob" should not be a member of group "trial_users"

  @backend-only
  Scenario: Cannot create user group with duplicate name
    Given a user group "existing_group" exists with description "Existing"
    When I try to create a user group "existing_group" with description "Duplicate"
    Then I should receive a "DuplicateUserGroupError"

  @backend-only
  Scenario: Cannot create user group with empty name
    When I try to create a user group "" with description "No name"
    Then I should receive a "ValueError"

  @backend-only
  Scenario: Cannot create user group as Customer
    Given I am logged in as a Customer
    When I try to create a user group "my_group" with description "My group"
    Then I should receive a "PermissionDeniedError"

  @backend-only
  Scenario: Cannot delete user group as Customer
    Given a user group "protected_group" exists with description "Protected"
    And I am logged in as a Customer
    When I try to delete the user group "protected_group"
    Then I should receive a "PermissionDeniedError"

  @backend-only
  Scenario: Cannot add user to group as Customer
    Given a user group "admin_managed" exists with description "Admin managed"
    And a customer "charlie" exists
    And I am logged in as a Customer
    When I try to add user "charlie" to the group "admin_managed"
    Then I should receive a "PermissionDeniedError"
