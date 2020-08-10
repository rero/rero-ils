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
  cy.fixture('users').then(function (userData) {
    this.users = userData;
  });
  cy.fixture('common').then(function (commonData) {
    this.common = commonData;
  });
})


describe('Acquisition - Budget', function() {
  it('Create-Delete a budget', function() {

    // Use one budget (between 2021 and 2050)
    let budget_name = 2020 + Math.floor((Math.random() * 29) + 1);

    cy.setup()
    cy.adminLogin(this.users.sysLibrarians.astrid.email, this.common.uniquePwd);

    // Go to Budgets Screen
    cy.goToMenu('budgets-menu-frontpage')

    // Click on "Add" button to create a new budget
    cy.get('#search-add-button').click()

    // Fill in the budget Form
    cy.get('#name').type(budget_name.toString())
    cy.get('#start_date').type(budget_name.toString() + '-01-01')
    cy.get('#start_date').click()
    cy.get('#end_date').type(budget_name.toString() + '-12-31')
    cy.get('#end_date').click()
    cy.get('#start_date').click()

    // Save the budget
    cy.get('#editor-save-button').click()
    cy.wait(1000)

    // Assert that the budget has been created
    cy.get('.mb-1').should('contain', budget_name)

    // Delete the budget
    // TO DO - Not yet implemented in the UI

  });
})
