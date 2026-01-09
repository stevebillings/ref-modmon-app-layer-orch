Feature: Incident Notifications
  As a System Administrator
  I want server incidents to trigger email notifications
  So that I can respond quickly to production issues

  Background:
    Given I am logged in as an Admin
    And incident notification recipients are configured

  @backend-only
  Scenario: Send notification when feature flag is enabled
    Given the feature flag "incident_email_notifications" is enabled
    When a server incident occurs
    Then an incident notification email should be sent
    And the email should contain the error details

  @backend-only
  Scenario: Skip notification when feature flag is disabled
    Given the feature flag "incident_email_notifications" is disabled
    When a server incident occurs
    Then no incident notification email should be sent

  @backend-only
  Scenario: Send notification to user in target group
    Given a user group "ops_team" exists with description "Operations team"
    And the feature flag "incident_email_notifications" is enabled
    And the flag "incident_email_notifications" has target group "ops_team"
    And a customer "ops_user" exists
    And user "ops_user" is a member of group "ops_team"
    When a server incident occurs for user "ops_user"
    Then an incident notification email should be sent

  @backend-only
  Scenario: Skip notification for user not in target group
    Given a user group "ops_team" exists with description "Operations team"
    And the feature flag "incident_email_notifications" is enabled
    And the flag "incident_email_notifications" has target group "ops_team"
    And a customer "regular_user" exists
    When a server incident occurs for user "regular_user"
    Then no incident notification email should be sent

  @backend-only
  Scenario: Notification includes request details
    Given the feature flag "incident_email_notifications" is enabled
    When a server incident occurs on path "/api/products/" with method "POST"
    Then an incident notification email should be sent
    And the email should contain request path "/api/products/"
    And the email should contain request method "POST"

  @backend-only
  Scenario: Notification includes error information
    Given the feature flag "incident_email_notifications" is enabled
    When a server incident occurs with error type "ValueError" and message "Invalid input"
    Then an incident notification email should be sent
    And the email should contain error type "ValueError"
    And the email should contain error message "Invalid input"

  @backend-only
  Scenario: Skip notification when no recipients configured
    Given the feature flag "incident_email_notifications" is enabled
    And no incident notification recipients are configured
    When a server incident occurs
    Then no incident notification email should be sent
    And a warning should be logged about missing recipients
