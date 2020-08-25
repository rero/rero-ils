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

// Pull data from common.json and users.json
beforeEach(function () {
  cy.fixture('users').then(function (userData) {
    this.users = userData;
  })
  cy.fixture('common').then(function (commonData) {
    this.common = commonData;
  })
})

describe('Circulation checkout checkin', function() {
  it.skip('Performs a checkout and a checkin', function() {

    const virgile = this.users.librarians.virgile;
    const simonetta = this.users.patrons.simonetta;
    const password = this.common.uniquePwd;
    const patronBarcode = '2050124311'
    const itemBarcode = 'checkout-checkin' + cy.getCurrentDateAndHour()

    cy.setLanguageToEnglish()
    cy.adminLogin(virgile.email, password)

    // Create an item
    cy.createItem(itemBarcode, 'Standard', 'Espaces publics')

    // Go to Circulation
    cy.goToMenu('circulation-menu-frontpage')

    // Checkout
    cy.scanPatronBarcodeThenItemBarcode(patronBarcode, simonetta, itemBarcode);

    // Assert checkout
    cy.get('#item-' + itemBarcode + ' > .row > [name="barcode"]')
      .should('contain', itemBarcode)
    cy.get('#item-' + itemBarcode + ' > .row > [name="action-done"] > i')
      .should('have.class', 'fa-arrow-circle-o-right')

    // Checkin
    cy.scanItemBarcode(itemBarcode);

    // Assert checkin
    cy.get('#item-' + itemBarcode + ' > .row > [name="barcode"]')
      .should('contain', itemBarcode)
    cy.get('#item-' + itemBarcode + ' > .row > [name="action-done"] > i')
      .should('have.class', 'fa-arrow-circle-o-down')

    // Go back to homepage, search document and delete item
    cy.goToDocumentDetailView(itemBarcode)
    // click on Delete button
    cy.get('#item-' + itemBarcode + ' > [name=buttons] > button[name=delete]').click();
    // Then confirm
    cy.get('#modal-confirm-button').click()
  });
})
