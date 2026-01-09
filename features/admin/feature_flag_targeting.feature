Feature: Feature Flag Targeting
  As an Admin
  I want to target feature flags to specific user groups
  So that I can roll out features to selected users

  Background:
    Given I am logged in as an Admin

  @backend @frontend
  Scenario: Add target group to a feature flag
    Given a feature flag "beta_feature" exists with enabled "true"
    And a user group "beta_testers" exists with description "Beta testers"
    When I add target group "beta_testers" to flag "beta_feature"
    Then the flag "beta_feature" should have target group "beta_testers"

  @backend @frontend
  Scenario: Remove target group from a feature flag
    Given a feature flag "limited_feature" exists with enabled "true"
    And a user group "internal" exists with description "Internal users"
    And the flag "limited_feature" has target group "internal"
    When I remove target group "internal" from flag "limited_feature"
    Then the flag "limited_feature" should not have target group "internal"

  @backend @frontend
  Scenario: Set multiple target groups for a feature flag
    Given a feature flag "premium_feature" exists with enabled "true"
    And a user group "premium_users" exists with description "Premium users"
    And a user group "early_adopters" exists with description "Early adopters"
    When I set target groups "premium_users, early_adopters" for flag "premium_feature"
    Then the flag "premium_feature" should have target group "premium_users"
    And the flag "premium_feature" should have target group "early_adopters"

  @backend-only
  Scenario: Targeted flag is enabled for user in target group
    Given a feature flag "targeted_feature" exists with enabled "true"
    And a user group "test_group" exists with description "Test group"
    And the flag "targeted_feature" has target group "test_group"
    And a customer "alice" exists
    And user "alice" is a member of group "test_group"
    When I check if flag "targeted_feature" is enabled for user "alice"
    Then the flag should be enabled

  @backend-only
  Scenario: Targeted flag is disabled for user not in target group
    Given a feature flag "exclusive_feature" exists with enabled "true"
    And a user group "exclusive_group" exists with description "Exclusive"
    And the flag "exclusive_feature" has target group "exclusive_group"
    And a customer "bob" exists
    When I check if flag "exclusive_feature" is enabled for user "bob"
    Then the flag should be disabled

  @backend-only
  Scenario: Flag without targets is enabled for all users when enabled
    Given a feature flag "global_feature" exists with enabled "true"
    And a customer "charlie" exists
    When I check if flag "global_feature" is enabled for user "charlie"
    Then the flag should be enabled

  @backend-only
  Scenario: Disabled flag is disabled for all users regardless of targeting
    Given a feature flag "disabled_targeted" exists with enabled "false"
    And a user group "all_users" exists with description "All users"
    And the flag "disabled_targeted" has target group "all_users"
    And a customer "dave" exists
    And user "dave" is a member of group "all_users"
    When I check if flag "disabled_targeted" is enabled for user "dave"
    Then the flag should be disabled

  @backend-only
  Scenario: User in multiple groups matches targeted flag
    Given a feature flag "multi_group_feature" exists with enabled "true"
    And a user group "group_a" exists with description "Group A"
    And a user group "group_b" exists with description "Group B"
    And the flag "multi_group_feature" has target group "group_a"
    And a customer "eve" exists
    And user "eve" is a member of group "group_b"
    And user "eve" is a member of group "group_a"
    When I check if flag "multi_group_feature" is enabled for user "eve"
    Then the flag should be enabled

  @backend-only
  Scenario: Clear all target groups from a flag
    Given a feature flag "clearable_feature" exists with enabled "true"
    And a user group "temp_group" exists with description "Temporary"
    And the flag "clearable_feature" has target group "temp_group"
    When I clear all target groups from flag "clearable_feature"
    Then the flag "clearable_feature" should have no target groups

  @backend-only
  Scenario: Cannot add target group as Customer
    Given a feature flag "admin_only_targeting" exists with enabled "true"
    And a user group "some_group" exists with description "Some group"
    And I am logged in as a Customer
    When I try to add target group "some_group" to flag "admin_only_targeting"
    Then I should receive a "PermissionDeniedError"
