Feature: Feature Flags
  As an Admin
  I want to manage feature flags
  So that I can control feature rollouts without code deployments

  Background:
    Given I am logged in as an Admin

  @backend @frontend
  Scenario: Successfully create a feature flag
    When I create a feature flag "dark_mode" with description "Enable dark mode UI"
    Then the feature flag "dark_mode" should exist
    And the feature flag "dark_mode" should be disabled
    And the feature flag "dark_mode" should have description "Enable dark mode UI"

  @backend @frontend
  Scenario: Enable a feature flag
    Given a feature flag "beta_features" exists and is disabled
    When I enable the feature flag "beta_features"
    Then the feature flag "beta_features" should be enabled

  @backend @frontend
  Scenario: Disable a feature flag
    Given a feature flag "old_feature" exists and is enabled
    When I disable the feature flag "old_feature"
    Then the feature flag "old_feature" should be disabled

  @backend @frontend
  Scenario: Delete a feature flag
    Given a feature flag "temporary_flag" exists and is disabled
    When I delete the feature flag "temporary_flag"
    Then the feature flag "temporary_flag" should not exist

  @backend-only
  Scenario: Cannot create feature flag with duplicate name
    Given a feature flag "existing_flag" exists and is disabled
    When I try to create a feature flag "existing_flag" with description "Duplicate"
    Then I should receive a "DuplicateFeatureFlagError"

  @backend-only
  Scenario: Cannot create feature flag as Customer
    Given I am logged in as a Customer
    When I try to create a feature flag "secret_feature" with description "Secret"
    Then I should receive a "PermissionDeniedError"

  @backend-only
  Scenario: Cannot enable feature flag as Customer
    Given a feature flag "admin_only" exists and is disabled
    And I am logged in as a Customer
    When I try to enable the feature flag "admin_only"
    Then I should receive a "PermissionDeniedError"

  @backend-only
  Scenario: Cannot delete feature flag as Customer
    Given a feature flag "protected_flag" exists and is disabled
    And I am logged in as a Customer
    When I try to delete the feature flag "protected_flag"
    Then I should receive a "PermissionDeniedError"
