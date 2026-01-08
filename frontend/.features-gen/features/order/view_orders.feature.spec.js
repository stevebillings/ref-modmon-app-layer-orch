// Generated from: ../features/order/view_orders.feature
import { test } from "../../../e2e/fixtures/test-fixtures.ts";

test.describe('View Orders', () => {

  test('Customer sees only their own orders', { tag: ['@backend', '@frontend'] }, async ({ Given, When, Then, And, apiClient, page, testContext }) => { 
    await Given('a customer "alice" has submitted an order for "Widget" at "$19.99" quantity 2', null, { apiClient, testContext }); 
    await And('a customer "bob" has submitted an order for "Gadget" at "$29.99" quantity 1', null, { apiClient, testContext }); 
    await When('I am logged in as customer "alice"', null, { apiClient, page, testContext }); 
    await And('I view my orders', null, { page }); 
    await Then('I should see 1 order', null, { page }); 
    await And('the order should contain "Widget" quantity 2', null, { page }); 
  });

  test('Admin sees all orders', { tag: ['@backend', '@frontend'] }, async ({ Given, When, Then, And, apiClient, page, testContext }) => { 
    await Given('a customer "alice" has submitted an order for "Widget" at "$19.99" quantity 2', null, { apiClient, testContext }); 
    await And('a customer "bob" has submitted an order for "Gadget" at "$29.99" quantity 1', null, { apiClient, testContext }); 
    await When('I am logged in as an Admin', null, { apiClient, page }); 
    await And('I view all orders', null, { page }); 
    await Then('I should see 2 orders', null, { page }); 
  });

  test('No orders shows empty list', { tag: ['@backend', '@frontend'] }, async ({ Given, When, Then, And, apiClient, page }) => { 
    await Given('I am logged in as a Customer', null, { apiClient, page }); 
    await And('I have no previous orders'); 
    await When('I view my orders', null, { page }); 
    await Then('I should see 0 orders', null, { page }); 
  });

});

// == technical section ==

test.use({
  $test: [({}, use) => use(test), { scope: 'test', box: true }],
  $uri: [({}, use) => use('../features/order/view_orders.feature'), { scope: 'test', box: true }],
  $bddFileData: [({}, use) => use(bddFileData), { scope: "test", box: true }],
});

const bddFileData = [ // bdd-data-start
  {"pwTestLine":6,"pickleLine":7,"tags":["@backend","@frontend"],"steps":[{"pwStepLine":7,"gherkinStepLine":8,"keywordType":"Context","textWithKeyword":"Given a customer \"alice\" has submitted an order for \"Widget\" at \"$19.99\" quantity 2","stepMatchArguments":[{"group":{"start":11,"value":"\"alice\"","children":[{"start":12,"value":"alice","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":46,"value":"\"Widget\"","children":[{"start":47,"value":"Widget","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":58,"value":"\"$19.99\"","children":[{"start":59,"value":"$19.99","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":76,"value":"2","children":[]},"parameterTypeName":"int"}]},{"pwStepLine":8,"gherkinStepLine":9,"keywordType":"Context","textWithKeyword":"And a customer \"bob\" has submitted an order for \"Gadget\" at \"$29.99\" quantity 1","stepMatchArguments":[{"group":{"start":11,"value":"\"bob\"","children":[{"start":12,"value":"bob","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":44,"value":"\"Gadget\"","children":[{"start":45,"value":"Gadget","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":56,"value":"\"$29.99\"","children":[{"start":57,"value":"$29.99","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":74,"value":"1","children":[]},"parameterTypeName":"int"}]},{"pwStepLine":9,"gherkinStepLine":10,"keywordType":"Action","textWithKeyword":"When I am logged in as customer \"alice\"","stepMatchArguments":[{"group":{"start":27,"value":"\"alice\"","children":[{"start":28,"value":"alice","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":10,"gherkinStepLine":11,"keywordType":"Action","textWithKeyword":"And I view my orders","stepMatchArguments":[]},{"pwStepLine":11,"gherkinStepLine":12,"keywordType":"Outcome","textWithKeyword":"Then I should see 1 order","stepMatchArguments":[{"group":{"start":13,"value":"1","children":[]},"parameterTypeName":"int"}]},{"pwStepLine":12,"gherkinStepLine":13,"keywordType":"Outcome","textWithKeyword":"And the order should contain \"Widget\" quantity 2","stepMatchArguments":[{"group":{"start":25,"value":"\"Widget\"","children":[{"start":26,"value":"Widget","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":43,"value":"2","children":[]},"parameterTypeName":"int"}]}]},
  {"pwTestLine":15,"pickleLine":16,"tags":["@backend","@frontend"],"steps":[{"pwStepLine":16,"gherkinStepLine":17,"keywordType":"Context","textWithKeyword":"Given a customer \"alice\" has submitted an order for \"Widget\" at \"$19.99\" quantity 2","stepMatchArguments":[{"group":{"start":11,"value":"\"alice\"","children":[{"start":12,"value":"alice","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":46,"value":"\"Widget\"","children":[{"start":47,"value":"Widget","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":58,"value":"\"$19.99\"","children":[{"start":59,"value":"$19.99","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":76,"value":"2","children":[]},"parameterTypeName":"int"}]},{"pwStepLine":17,"gherkinStepLine":18,"keywordType":"Context","textWithKeyword":"And a customer \"bob\" has submitted an order for \"Gadget\" at \"$29.99\" quantity 1","stepMatchArguments":[{"group":{"start":11,"value":"\"bob\"","children":[{"start":12,"value":"bob","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":44,"value":"\"Gadget\"","children":[{"start":45,"value":"Gadget","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":56,"value":"\"$29.99\"","children":[{"start":57,"value":"$29.99","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":74,"value":"1","children":[]},"parameterTypeName":"int"}]},{"pwStepLine":18,"gherkinStepLine":19,"keywordType":"Action","textWithKeyword":"When I am logged in as an Admin","stepMatchArguments":[]},{"pwStepLine":19,"gherkinStepLine":20,"keywordType":"Action","textWithKeyword":"And I view all orders","stepMatchArguments":[]},{"pwStepLine":20,"gherkinStepLine":21,"keywordType":"Outcome","textWithKeyword":"Then I should see 2 orders","stepMatchArguments":[{"group":{"start":13,"value":"2","children":[]},"parameterTypeName":"int"}]}]},
  {"pwTestLine":23,"pickleLine":32,"tags":["@backend","@frontend"],"steps":[{"pwStepLine":24,"gherkinStepLine":33,"keywordType":"Context","textWithKeyword":"Given I am logged in as a Customer","stepMatchArguments":[]},{"pwStepLine":25,"gherkinStepLine":34,"keywordType":"Context","textWithKeyword":"And I have no previous orders","stepMatchArguments":[]},{"pwStepLine":26,"gherkinStepLine":35,"keywordType":"Action","textWithKeyword":"When I view my orders","stepMatchArguments":[]},{"pwStepLine":27,"gherkinStepLine":36,"keywordType":"Outcome","textWithKeyword":"Then I should see 0 orders","stepMatchArguments":[{"group":{"start":13,"value":"0","children":[]},"parameterTypeName":"int"}]}]},
]; // bdd-data-end