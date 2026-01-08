// Generated from: ../features/cart/remove_from_cart.feature
import { test } from "../../../e2e/fixtures/test-fixtures.ts";

test.describe('Remove Item from Cart', () => {

  test.beforeEach('Background', async ({ Given, And, apiClient, page, testContext }, testInfo) => { if (testInfo.error) return;
    await Given('I am logged in as a Customer', null, { apiClient, page }); 
    await And('a product "Keyboard" exists with price "$79.99" and stock quantity 30', null, { apiClient, testContext }); 
    await And('my cart contains 5 "Keyboard"', null, { apiClient, testContext }); 
  });
  
  test('Successfully remove item from cart', { tag: ['@backend', '@frontend'] }, async ({ When, Then, page }) => { 
    await When('I remove "Keyboard" from my cart', null, { page }); 
    await Then('my cart should be empty', null, { page }); 
  });

});

// == technical section ==

test.use({
  $test: [({}, use) => use(test), { scope: 'test', box: true }],
  $uri: [({}, use) => use('../features/cart/remove_from_cart.feature'), { scope: 'test', box: true }],
  $bddFileData: [({}, use) => use(bddFileData), { scope: "test", box: true }],
});

const bddFileData = [ // bdd-data-start
  {"pwTestLine":12,"pickleLine":12,"tags":["@backend","@frontend"],"steps":[{"pwStepLine":7,"gherkinStepLine":7,"keywordType":"Context","textWithKeyword":"Given I am logged in as a Customer","isBg":true,"stepMatchArguments":[]},{"pwStepLine":8,"gherkinStepLine":8,"keywordType":"Context","textWithKeyword":"And a product \"Keyboard\" exists with price \"$79.99\" and stock quantity 30","isBg":true,"stepMatchArguments":[{"group":{"start":10,"value":"\"Keyboard\"","children":[{"start":11,"value":"Keyboard","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":39,"value":"\"$79.99\"","children":[{"start":40,"value":"$79.99","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":67,"value":"30","children":[]},"parameterTypeName":"int"}]},{"pwStepLine":9,"gherkinStepLine":9,"keywordType":"Context","textWithKeyword":"And my cart contains 5 \"Keyboard\"","isBg":true,"stepMatchArguments":[{"group":{"start":17,"value":"5","children":[]},"parameterTypeName":"int"},{"group":{"start":19,"value":"\"Keyboard\"","children":[{"start":20,"value":"Keyboard","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":13,"gherkinStepLine":13,"keywordType":"Action","textWithKeyword":"When I remove \"Keyboard\" from my cart","stepMatchArguments":[{"group":{"start":9,"value":"\"Keyboard\"","children":[{"start":10,"value":"Keyboard","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":14,"gherkinStepLine":14,"keywordType":"Outcome","textWithKeyword":"Then my cart should be empty","stepMatchArguments":[]}]},
]; // bdd-data-end