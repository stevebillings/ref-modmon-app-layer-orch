// Generated from: ../features/product/create_product.feature
import { test } from "../../../e2e/fixtures/test-fixtures.ts";

test.describe('Create Product', () => {

  test.beforeEach('Background', async ({ Given, apiClient, page }, testInfo) => { if (testInfo.error) return;
    await Given('I am logged in as an Admin', null, { apiClient, page }); 
  });
  
  test('Successfully create a product', { tag: ['@backend', '@frontend'] }, async ({ When, Then, And, page }) => { 
    await When('I create a product with name "Widget Pro" price "$29.99" and stock quantity 100', null, { page }); 
    await Then('the product "Widget Pro" should exist', null, { page }); 
    await And('the product "Widget Pro" should have price "$29.99"', null, { page }); 
    await And('the product "Widget Pro" should have stock quantity 100', null, { page }); 
  });

});

// == technical section ==

test.use({
  $test: [({}, use) => use(test), { scope: 'test', box: true }],
  $uri: [({}, use) => use('../features/product/create_product.feature'), { scope: 'test', box: true }],
  $bddFileData: [({}, use) => use(bddFileData), { scope: "test", box: true }],
});

const bddFileData = [ // bdd-data-start
  {"pwTestLine":10,"pickleLine":10,"tags":["@backend","@frontend"],"steps":[{"pwStepLine":7,"gherkinStepLine":7,"keywordType":"Context","textWithKeyword":"Given I am logged in as an Admin","isBg":true,"stepMatchArguments":[]},{"pwStepLine":11,"gherkinStepLine":11,"keywordType":"Action","textWithKeyword":"When I create a product with name \"Widget Pro\" price \"$29.99\" and stock quantity 100","stepMatchArguments":[{"group":{"start":29,"value":"\"Widget Pro\"","children":[{"start":30,"value":"Widget Pro","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":48,"value":"\"$29.99\"","children":[{"start":49,"value":"$29.99","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":76,"value":"100","children":[]},"parameterTypeName":"int"}]},{"pwStepLine":12,"gherkinStepLine":12,"keywordType":"Outcome","textWithKeyword":"Then the product \"Widget Pro\" should exist","stepMatchArguments":[{"group":{"start":12,"value":"\"Widget Pro\"","children":[{"start":13,"value":"Widget Pro","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":13,"gherkinStepLine":13,"keywordType":"Outcome","textWithKeyword":"And the product \"Widget Pro\" should have price \"$29.99\"","stepMatchArguments":[{"group":{"start":12,"value":"\"Widget Pro\"","children":[{"start":13,"value":"Widget Pro","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":43,"value":"\"$29.99\"","children":[{"start":44,"value":"$29.99","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":14,"gherkinStepLine":14,"keywordType":"Outcome","textWithKeyword":"And the product \"Widget Pro\" should have stock quantity 100","stepMatchArguments":[{"group":{"start":12,"value":"\"Widget Pro\"","children":[{"start":13,"value":"Widget Pro","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":52,"value":"100","children":[]},"parameterTypeName":"int"}]}]},
]; // bdd-data-end