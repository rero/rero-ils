/// <reference types="Cypress" />
/*

RERO ILS
Copyright (C) 2020 RERO

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

*/

before(function () {
  // Run once before all
  // Use to load fixtures and set variable needed in all tests
  cy.fixture('users').then(function (users) {
    this.users = users;
  });
  cy.fixture('common').then(function (common) {
    this.common = common;
  });
  cy.fixture('cipo').then(function (cipo) {
    this.cipo = cipo;
  });
  cy.fixture('item_types').then(function (itemTypes) {
    this.itemTypes = itemTypes;
  });
  cy.fixture('patron_types').then(function (patronTypes) {
    this.patronTypes = patronTypes;
  });
});

describe('Create and edit a circulation policy', function() {
  let cipoPid;

  before('Login and prepare app for tests', function() {
    // Login as librarian (Leonard)
    cy.adminLogin(this.users.librarians.leonard.email, this.common.uniquePwd);
  });

  beforeEach('Add description if needed', function() {
    // Preserve authentication information between the tests
    Cypress.Cookies.preserveOnce('session');
  });

  after('Clean data: ...', function() {
    // Remove circulation policy
    cy.get('#detail-delete-button').click();
    cy.get('#modal-confirm-button').click();
    cy.logout();
  });

  it('Creates an extended circulation policy', function() {
    cy.server();
    cy.route('/api/item_types/*').as('getItemTypes');
    cy.route('/api/patron_types/*').as('getpatronTypes');
    cy.route('POST', 'api/circ_policies').as('createCiPo');
    // Go to ci-po editor
    cy.get('#admin-and-monitoring-menu').click();
    cy.get('#circulation-policies-menu').click();
    cy.get('#search-add-button').click();
    // Fill the form with an existing name
    cy.get('#name').type(this.cipo.default.name);
    // Assert that the name uniqueness is highlighted
    cy.get('#cipo-name-unique').should('contain', 'This name is already taken.');
    cy.get('#name').clear();
    // Create a cipo
    cy.uiCreateOrUpdateCipo(this.cipo.extended, this.patronTypes.standard.pid, this.itemTypes.on_site.pid);
    // Assert that the ci-po has been correctly saved
    cy.wait('@createCiPo').its('response').then((res) => {
      cipoPid = res.body.id;
      cy.log('Circulation policy #' + cipoPid + ' created');
    });
    cy.wait(['@getItemTypes', '@getpatronTypes']);
    cy.checkCipoCreated(this.cipo.extended, this.patronTypes.standard.pid, this.itemTypes.on_site.pid);
  });
});
