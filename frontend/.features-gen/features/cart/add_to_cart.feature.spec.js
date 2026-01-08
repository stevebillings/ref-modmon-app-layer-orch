// Generated from: ../features/cart/add_to_cart.feature
import { test } from "../../../e2e/fixtures/test-fixtures.ts";

test.describe('Add Item to Cart', () => {

  test.beforeEach('Background', async ({ Given, And, apiClient, page, testContext }, testInfo) => { if (testInfo.error) return;
    await Given('I am logged in as a Customer', null, { apiClient, page }); 
    await And('a product "Laptop" exists with price "$999.99" and stock quantity 10', null, { apiClient, testContext }); 
  });
  
  test('Successfully add item to cart', { tag: ['@backend', '@frontend'] }, async ({ When, Then, page }) => { 
    await When('I add 2 "Laptop" to my cart', null, { page }); 
    await Then('my cart should contain 2 "Laptop" at "$999.99" each', null, { page }); 
  });

  test('Add same product twice merges quantities', { tag: ['@backend', '@frontend'] }, async ({ Given, When, Then, apiClient, page, testContext }) => { 
    await Given('my cart contains 2 "Laptop"', null, { apiClient, testContext }); 
    await When('I add 3 "Laptop" to my cart', null, { page }); 
    await Then('my cart should contain 5 "Laptop"', null, { page }); 
  });

});

// == technical section ==

test.use({
  $test: [({}, use) => use(test), { scope: 'test', box: true }],
  $uri: [({}, use) => use('../features/cart/add_to_cart.feature'), { scope: 'test', box: true }],
  $bddFileData: [({}, use) => use(bddFileData), { scope: "test", box: true }],
});

const bddFileData = [ // bdd-data-start
  {"pwTestLine":11,"pickleLine":11,"tags":["@backend","@frontend"],"steps":[{"pwStepLine":7,"gherkinStepLine":7,"keywordType":"Context","textWithKeyword":"Given I am logged in as a Customer","isBg":true,"stepMatchArguments":[]},{"pwStepLine":8,"gherkinStepLine":8,"keywordType":"Context","textWithKeyword":"And a product \"Laptop\" exists with price \"$999.99\" and stock quantity 10","isBg":true,"stepMatchArguments":[{"group":{"start":10,"value":"\"Laptop\"","children":[{"start":11,"value":"Laptop","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":37,"value":"\"$999.99\"","children":[{"start":38,"value":"$999.99","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":66,"value":"10","children":[]},"parameterTypeName":"int"}]},{"pwStepLine":12,"gherkinStepLine":12,"keywordType":"Action","textWithKeyword":"When I add 2 \"Laptop\" to my cart","stepMatchArguments":[{"group":{"start":6,"value":"2","children":[]},"parameterTypeName":"int"},{"group":{"start":8,"value":"\"Laptop\"","children":[{"start":9,"value":"Laptop","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":13,"gherkinStepLine":13,"keywordType":"Outcome","textWithKeyword":"Then my cart should contain 2 \"Laptop\" at \"$999.99\" each","stepMatchArguments":[{"group":{"start":23,"value":"2","children":[]},"parameterTypeName":"int"},{"group":{"start":25,"value":"\"Laptop\"","children":[{"start":26,"value":"Laptop","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":37,"value":"\"$999.99\"","children":[{"start":38,"value":"$999.99","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]}]},
  {"pwTestLine":16,"pickleLine":21,"tags":["@backend","@frontend"],"steps":[{"pwStepLine":7,"gherkinStepLine":7,"keywordType":"Context","textWithKeyword":"Given I am logged in as a Customer","isBg":true,"stepMatchArguments":[]},{"pwStepLine":8,"gherkinStepLine":8,"keywordType":"Context","textWithKeyword":"And a product \"Laptop\" exists with price \"$999.99\" and stock quantity 10","isBg":true,"stepMatchArguments":[{"group":{"start":10,"value":"\"Laptop\"","children":[{"start":11,"value":"Laptop","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":37,"value":"\"$999.99\"","children":[{"start":38,"value":"$999.99","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":66,"value":"10","children":[]},"parameterTypeName":"int"}]},{"pwStepLine":17,"gherkinStepLine":22,"keywordType":"Context","textWithKeyword":"Given my cart contains 2 \"Laptop\"","stepMatchArguments":[{"group":{"start":17,"value":"2","children":[]},"parameterTypeName":"int"},{"group":{"start":19,"value":"\"Laptop\"","children":[{"start":20,"value":"Laptop","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":18,"gherkinStepLine":23,"keywordType":"Action","textWithKeyword":"When I add 3 \"Laptop\" to my cart","stepMatchArguments":[{"group":{"start":6,"value":"3","children":[]},"parameterTypeName":"int"},{"group":{"start":8,"value":"\"Laptop\"","children":[{"start":9,"value":"Laptop","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":19,"gherkinStepLine":24,"keywordType":"Outcome","textWithKeyword":"Then my cart should contain 5 \"Laptop\"","stepMatchArguments":[{"group":{"start":23,"value":"5","children":[]},"parameterTypeName":"int"},{"group":{"start":25,"value":"\"Laptop\"","children":[{"start":26,"value":"Laptop","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]}]},
]; // bdd-data-end