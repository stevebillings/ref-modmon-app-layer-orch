// Generated from: ../features/product/delete_product.feature
import { test } from "../../../e2e/fixtures/test-fixtures.ts";

test.describe('Delete Product', () => {

  test.beforeEach('Background', async ({ Given, And, apiClient, page, testContext }, testInfo) => { if (testInfo.error) return;
    await Given('I am logged in as an Admin', null, { apiClient, page }); 
    await And('a product "Old Widget" exists with price "$10.00" and stock quantity 50', null, { apiClient, testContext }); 
  });
  
  test('Successfully soft delete a product', { tag: ['@backend', '@frontend'] }, async ({ When, Then, And, page }) => { 
    await When('I delete the product "Old Widget"', null, { page }); 
    await Then('the product "Old Widget" should be marked as deleted', null, { page }); 
    await And('the product "Old Widget" should not appear in the product catalog', null, { page }); 
  });

  test('Admin can see deleted products when including deleted', { tag: ['@backend', '@frontend'] }, async ({ When, Then, page }) => { 
    await When('I delete the product "Old Widget"', null, { page }); 
    await Then('the product "Old Widget" should appear when including deleted products', null, { page }); 
  });

  test('Can restore a deleted product', { tag: ['@backend', '@frontend'] }, async ({ Given, When, Then, apiClient, page, testContext }) => { 
    await Given('the product "Old Widget" has been deleted', null, { apiClient, testContext }); 
    await When('I restore the product "Old Widget"', null, { page }); 
    await Then('the product "Old Widget" should appear in the product catalog', null, { page }); 
  });

});

// == technical section ==

test.use({
  $test: [({}, use) => use(test), { scope: 'test', box: true }],
  $uri: [({}, use) => use('../features/product/delete_product.feature'), { scope: 'test', box: true }],
  $bddFileData: [({}, use) => use(bddFileData), { scope: "test", box: true }],
});

const bddFileData = [ // bdd-data-start
  {"pwTestLine":11,"pickleLine":11,"tags":["@backend","@frontend"],"steps":[{"pwStepLine":7,"gherkinStepLine":7,"keywordType":"Context","textWithKeyword":"Given I am logged in as an Admin","isBg":true,"stepMatchArguments":[]},{"pwStepLine":8,"gherkinStepLine":8,"keywordType":"Context","textWithKeyword":"And a product \"Old Widget\" exists with price \"$10.00\" and stock quantity 50","isBg":true,"stepMatchArguments":[{"group":{"start":10,"value":"\"Old Widget\"","children":[{"start":11,"value":"Old Widget","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":41,"value":"\"$10.00\"","children":[{"start":42,"value":"$10.00","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":69,"value":"50","children":[]},"parameterTypeName":"int"}]},{"pwStepLine":12,"gherkinStepLine":12,"keywordType":"Action","textWithKeyword":"When I delete the product \"Old Widget\"","stepMatchArguments":[{"group":{"start":21,"value":"\"Old Widget\"","children":[{"start":22,"value":"Old Widget","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":13,"gherkinStepLine":13,"keywordType":"Outcome","textWithKeyword":"Then the product \"Old Widget\" should be marked as deleted","stepMatchArguments":[{"group":{"start":12,"value":"\"Old Widget\"","children":[{"start":13,"value":"Old Widget","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":14,"gherkinStepLine":14,"keywordType":"Outcome","textWithKeyword":"And the product \"Old Widget\" should not appear in the product catalog","stepMatchArguments":[{"group":{"start":12,"value":"\"Old Widget\"","children":[{"start":13,"value":"Old Widget","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]}]},
  {"pwTestLine":17,"pickleLine":17,"tags":["@backend","@frontend"],"steps":[{"pwStepLine":7,"gherkinStepLine":7,"keywordType":"Context","textWithKeyword":"Given I am logged in as an Admin","isBg":true,"stepMatchArguments":[]},{"pwStepLine":8,"gherkinStepLine":8,"keywordType":"Context","textWithKeyword":"And a product \"Old Widget\" exists with price \"$10.00\" and stock quantity 50","isBg":true,"stepMatchArguments":[{"group":{"start":10,"value":"\"Old Widget\"","children":[{"start":11,"value":"Old Widget","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":41,"value":"\"$10.00\"","children":[{"start":42,"value":"$10.00","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":69,"value":"50","children":[]},"parameterTypeName":"int"}]},{"pwStepLine":18,"gherkinStepLine":18,"keywordType":"Action","textWithKeyword":"When I delete the product \"Old Widget\"","stepMatchArguments":[{"group":{"start":21,"value":"\"Old Widget\"","children":[{"start":22,"value":"Old Widget","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":19,"gherkinStepLine":19,"keywordType":"Outcome","textWithKeyword":"Then the product \"Old Widget\" should appear when including deleted products","stepMatchArguments":[{"group":{"start":12,"value":"\"Old Widget\"","children":[{"start":13,"value":"Old Widget","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]}]},
  {"pwTestLine":22,"pickleLine":36,"tags":["@backend","@frontend"],"steps":[{"pwStepLine":7,"gherkinStepLine":7,"keywordType":"Context","textWithKeyword":"Given I am logged in as an Admin","isBg":true,"stepMatchArguments":[]},{"pwStepLine":8,"gherkinStepLine":8,"keywordType":"Context","textWithKeyword":"And a product \"Old Widget\" exists with price \"$10.00\" and stock quantity 50","isBg":true,"stepMatchArguments":[{"group":{"start":10,"value":"\"Old Widget\"","children":[{"start":11,"value":"Old Widget","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":41,"value":"\"$10.00\"","children":[{"start":42,"value":"$10.00","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":69,"value":"50","children":[]},"parameterTypeName":"int"}]},{"pwStepLine":23,"gherkinStepLine":37,"keywordType":"Context","textWithKeyword":"Given the product \"Old Widget\" has been deleted","stepMatchArguments":[{"group":{"start":12,"value":"\"Old Widget\"","children":[{"start":13,"value":"Old Widget","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":24,"gherkinStepLine":38,"keywordType":"Action","textWithKeyword":"When I restore the product \"Old Widget\"","stepMatchArguments":[{"group":{"start":22,"value":"\"Old Widget\"","children":[{"start":23,"value":"Old Widget","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":25,"gherkinStepLine":39,"keywordType":"Outcome","textWithKeyword":"Then the product \"Old Widget\" should appear in the product catalog","stepMatchArguments":[{"group":{"start":12,"value":"\"Old Widget\"","children":[{"start":13,"value":"Old Widget","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]}]},
]; // bdd-data-end