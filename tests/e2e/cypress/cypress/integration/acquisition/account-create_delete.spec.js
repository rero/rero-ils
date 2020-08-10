/// <reference types="Cypress" />
/*

RERO ILS
Copyright (C) 2020 RERO
Copyright (C) 2020 UCLouvain

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
  cy.fixture('account').then(function (accountData) {
    this.account = accountData;
  });
  cy.fixture('users').then(function (userData) {
    this.users = userData;
  });
  cy.fixture('common').then(function (commonData) {
    this.common = commonData;
  });
})

describe('Acquisition - Account', function() {
  it('Create-Delete an account', function() {
    const account = this.account.account;

    cy.setup()
    cy.adminLogin(this.users.librarians.virgile.email, this.common.uniquePwd);

    // Go to Budgets Screen
    cy.goToMenu('budgets-menu-frontpage');

    // Click on the more recent year (top of the list)
    cy.get(':nth-child(1) > ng-core-record-search-result > admin-budgets-brief-view.ng-star-inserted > .card-title > .pr-1').click()
    cy.wait(1500)
    // Click on "Add" button to create a new account
    cy.get('.mt-4 > .btn').click()

    // Fill in the account Name
    cy.get('#name').type(account.name)
    cy.get('#description').type(account.description)
    cy.get('#amount_allocated').type(account.amount_allocated)
    cy.wait(800)
    cy.get('.btn-primary').click()
    cy.wait(3000)

    // Assert that the values are correctly displayed
    cy.get('admin-budget-detail-view.ng-star-inserted > :nth-child(3)').should('contain',account.name)

    // Delete the account
    cy.get(':nth-child(3) > .row > .col-sm-3 > .btn-outline-danger > .fa').click()
    cy.wait(800)
    cy.get('#modal-confirm-button').click()
    cy.wait(3000)

  });
})
