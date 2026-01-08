// Generated from: ../features/cart/submit_cart.feature
import { test } from "../../../e2e/fixtures/test-fixtures.ts";

test.describe('Submit Cart', () => {

  test.beforeEach('Background', async ({ Given, And, apiClient, page, testContext }, testInfo) => { if (testInfo.error) return;
    await Given('I am logged in as a Customer', null, { apiClient, page }); 
    await And('a product "Monitor" exists with price "$299.99" and stock quantity 15', null, { apiClient, testContext }); 
    await And('my cart contains 2 "Monitor"', null, { apiClient, testContext }); 
  });
  
  test('Successfully submit cart with verified address', { tag: ['@backend', '@frontend'] }, async ({ Given, When, Then, And, page, testContext }) => { 
    await Given('I have a valid shipping address:', {"dataTable":{"rows":[{"cells":[{"value":"street_line_1"},{"value":"city"},{"value":"state"},{"value":"postal_code"},{"value":"country"}]},{"cells":[{"value":"123 Main St"},{"value":"Portland"},{"value":"OR"},{"value":"97201"},{"value":"US"}]}]}}, { testContext }); 
    await When('I submit my cart', null, { page, testContext }); 
    await Then('an order should be created with 1 item totaling "$599.98"', null, { page }); 
    await And('my cart should be empty', null, { page }); 
    await And('the order should have a verified shipping address', null, { page }); 
  });

});

// == technical section ==

test.use({
  $test: [({}, use) => use(test), { scope: 'test', box: true }],
  $uri: [({}, use) => use('../features/cart/submit_cart.feature'), { scope: 'test', box: true }],
  $bddFileData: [({}, use) => use(bddFileData), { scope: "test", box: true }],
});

const bddFileData = [ // bdd-data-start
  {"pwTestLine":12,"pickleLine":12,"tags":["@backend","@frontend"],"steps":[{"pwStepLine":7,"gherkinStepLine":7,"keywordType":"Context","textWithKeyword":"Given I am logged in as a Customer","isBg":true,"stepMatchArguments":[]},{"pwStepLine":8,"gherkinStepLine":8,"keywordType":"Context","textWithKeyword":"And a product \"Monitor\" exists with price \"$299.99\" and stock quantity 15","isBg":true,"stepMatchArguments":[{"group":{"start":10,"value":"\"Monitor\"","children":[{"start":11,"value":"Monitor","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":38,"value":"\"$299.99\"","children":[{"start":39,"value":"$299.99","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":67,"value":"15","children":[]},"parameterTypeName":"int"}]},{"pwStepLine":9,"gherkinStepLine":9,"keywordType":"Context","textWithKeyword":"And my cart contains 2 \"Monitor\"","isBg":true,"stepMatchArguments":[{"group":{"start":17,"value":"2","children":[]},"parameterTypeName":"int"},{"group":{"start":19,"value":"\"Monitor\"","children":[{"start":20,"value":"Monitor","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":13,"gherkinStepLine":13,"keywordType":"Context","textWithKeyword":"Given I have a valid shipping address:","stepMatchArguments":[]},{"pwStepLine":14,"gherkinStepLine":16,"keywordType":"Action","textWithKeyword":"When I submit my cart","stepMatchArguments":[]},{"pwStepLine":15,"gherkinStepLine":17,"keywordType":"Outcome","textWithKeyword":"Then an order should be created with 1 item totaling \"$599.98\"","stepMatchArguments":[{"group":{"start":32,"value":"1","children":[]},"parameterTypeName":"int"},{"group":{"start":48,"value":"\"$599.98\"","children":[{"start":49,"value":"$599.98","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":16,"gherkinStepLine":18,"keywordType":"Outcome","textWithKeyword":"And my cart should be empty","stepMatchArguments":[]},{"pwStepLine":17,"gherkinStepLine":19,"keywordType":"Outcome","textWithKeyword":"And the order should have a verified shipping address","stepMatchArguments":[]}]},
]; // bdd-data-end