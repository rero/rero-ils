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
  cy.fixture('users').then(function (userData) {
    this.users = userData;
  });
  cy.fixture('common').then(function (commonData) {
    this.common = commonData;
  });
});

describe('Login and logout', function() {
  before('Go to frontpage', function() {
    cy.visit('/lang/en');
  });

  beforeEach('Add description if needed', function() {
    // Preserve authentication information between the tests
    Cypress.Cookies.preserveOnce('session');
  });

  after('Logout', function() {
    cy.logout();
  });

  it('Login as a librarian', function() {
    // Login
    cy.get('#my-account-menu').click();
    cy.wait(1000);
    cy.get('#login-menu').click();
    // Fill the form and submit
    cy.get('#email').type(this.users.librarians.leonard.email);
    cy.get('#password').type(this.common.uniquePwd);
    cy.get('form[name="login_user_form"]').submit();
    // Check that the user is logged
    cy.get('#my-account-menu').should('contain', this.users.librarians.leonard.initials);
    // Check professional interface access
    cy.visit('/professional');
    cy.get('body').should('contain','RERO ILS administration');
  });

  it('Logout', function() {
    // Click on username
    cy.get('#my-account-menu').click()
    // Wait for the menu to open
    cy.wait(1000)
    // Click on logout
    cy.get('#logout-menu').click();
    // Check that the user is logged out
    cy.get('body').should('contain','My account');
  });

  it('Login as a patron', function() {
    cy.get('#my-account-menu').click();
    cy.wait(1000);
    cy.get('#login-menu').click();
    // Fill the form
    cy.get('#email').type(this.users.patrons.james.email);
    cy.get('#password').type(this.common.uniquePwd);
    cy.get('form[name="login_user_form"]').submit();
    // Check that the user is logged
    cy.get('#my-account-menu').should('contain', this.users.patrons.james.initials);
  });
});
