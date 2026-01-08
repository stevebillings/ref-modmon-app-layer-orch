// Generated from: ../features/cart/update_cart_item.feature
import { test } from "../../../e2e/fixtures/test-fixtures.ts";

test.describe('Update Cart Item Quantity', () => {

  test.beforeEach('Background', async ({ Given, And, apiClient, page, testContext }, testInfo) => { if (testInfo.error) return;
    await Given('I am logged in as a Customer', null, { apiClient, page }); 
    await And('a product "Headphones" exists with price "$149.99" and stock quantity 20', null, { apiClient, testContext }); 
    await And('my cart contains 5 "Headphones"', null, { apiClient, testContext }); 
  });
  
  test('Increase item quantity', { tag: ['@backend', '@frontend'] }, async ({ When, Then, page }) => { 
    await When('I update "Headphones" quantity to 8', null, { page }); 
    await Then('my cart should contain 8 "Headphones"', null, { page }); 
  });

  test('Decrease item quantity', { tag: ['@backend', '@frontend'] }, async ({ When, Then, page }) => { 
    await When('I update "Headphones" quantity to 2', null, { page }); 
    await Then('my cart should contain 2 "Headphones"', null, { page }); 
  });

});

// == technical section ==

test.use({
  $test: [({}, use) => use(test), { scope: 'test', box: true }],
  $uri: [({}, use) => use('../features/cart/update_cart_item.feature'), { scope: 'test', box: true }],
  $bddFileData: [({}, use) => use(bddFileData), { scope: "test", box: true }],
});

const bddFileData = [ // bdd-data-start
  {"pwTestLine":12,"pickleLine":12,"tags":["@backend","@frontend"],"steps":[{"pwStepLine":7,"gherkinStepLine":7,"keywordType":"Context","textWithKeyword":"Given I am logged in as a Customer","isBg":true,"stepMatchArguments":[]},{"pwStepLine":8,"gherkinStepLine":8,"keywordType":"Context","textWithKeyword":"And a product \"Headphones\" exists with price \"$149.99\" and stock quantity 20","isBg":true,"stepMatchArguments":[{"group":{"start":10,"value":"\"Headphones\"","children":[{"start":11,"value":"Headphones","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":41,"value":"\"$149.99\"","children":[{"start":42,"value":"$149.99","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":70,"value":"20","children":[]},"parameterTypeName":"int"}]},{"pwStepLine":9,"gherkinStepLine":9,"keywordType":"Context","textWithKeyword":"And my cart contains 5 \"Headphones\"","isBg":true,"stepMatchArguments":[{"group":{"start":17,"value":"5","children":[]},"parameterTypeName":"int"},{"group":{"start":19,"value":"\"Headphones\"","children":[{"start":20,"value":"Headphones","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":13,"gherkinStepLine":13,"keywordType":"Action","textWithKeyword":"When I update \"Headphones\" quantity to 8","stepMatchArguments":[{"group":{"start":9,"value":"\"Headphones\"","children":[{"start":10,"value":"Headphones","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":34,"value":"8","children":[]},"parameterTypeName":"int"}]},{"pwStepLine":14,"gherkinStepLine":14,"keywordType":"Outcome","textWithKeyword":"Then my cart should contain 8 \"Headphones\"","stepMatchArguments":[{"group":{"start":23,"value":"8","children":[]},"parameterTypeName":"int"},{"group":{"start":25,"value":"\"Headphones\"","children":[{"start":26,"value":"Headphones","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]}]},
  {"pwTestLine":17,"pickleLine":22,"tags":["@backend","@frontend"],"steps":[{"pwStepLine":7,"gherkinStepLine":7,"keywordType":"Context","textWithKeyword":"Given I am logged in as a Customer","isBg":true,"stepMatchArguments":[]},{"pwStepLine":8,"gherkinStepLine":8,"keywordType":"Context","textWithKeyword":"And a product \"Headphones\" exists with price \"$149.99\" and stock quantity 20","isBg":true,"stepMatchArguments":[{"group":{"start":10,"value":"\"Headphones\"","children":[{"start":11,"value":"Headphones","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":41,"value":"\"$149.99\"","children":[{"start":42,"value":"$149.99","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":70,"value":"20","children":[]},"parameterTypeName":"int"}]},{"pwStepLine":9,"gherkinStepLine":9,"keywordType":"Context","textWithKeyword":"And my cart contains 5 \"Headphones\"","isBg":true,"stepMatchArguments":[{"group":{"start":17,"value":"5","children":[]},"parameterTypeName":"int"},{"group":{"start":19,"value":"\"Headphones\"","children":[{"start":20,"value":"Headphones","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":18,"gherkinStepLine":23,"keywordType":"Action","textWithKeyword":"When I update \"Headphones\" quantity to 2","stepMatchArguments":[{"group":{"start":9,"value":"\"Headphones\"","children":[{"start":10,"value":"Headphones","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":34,"value":"2","children":[]},"parameterTypeName":"int"}]},{"pwStepLine":19,"gherkinStepLine":24,"keywordType":"Outcome","textWithKeyword":"Then my cart should contain 2 \"Headphones\"","stepMatchArguments":[{"group":{"start":23,"value":"2","children":[]},"parameterTypeName":"int"},{"group":{"start":25,"value":"\"Headphones\"","children":[{"start":26,"value":"Headphones","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]}]},
]; // bdd-data-end