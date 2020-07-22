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

describe('Circulation checkout checkin', function() {
  it('Performs a checkout and a checkin', function() {

    const librarianEmail = 'reroilstest+virgile@gmail.com'
    const librarianPwd = '123456'
    const patronBarcode = '2050124311'
    const patronInfo = 'Casalini, Simonetta'
    const documentUrl = '/professional/records/documents/detail/253'
    const circUrl = '/professional/circulation/checkout'
    const itemBarcode = 'checkout-checkin'
    const timeOut = 3000;

    cy.setup()
    cy.adminLogin(librarianEmail, librarianPwd)

    // Create an item
    cy.createItem(itemBarcode, 'Standard', 'Espaces publics')

    // Go to Circulation
    cy.goToMenu('circulation-menu-frontpage')

    // Enter a patron barcode
    cy.get('#search', {timeout: timeOut})
      .type(patronBarcode)
      .type('{enter}')

    // Assert that patron info is displayed
    cy.wait(3000)
    cy.get(':nth-child(2) > :nth-child(1) > .col-md-10', {timeout: timeOut})
      .should('contain', patronInfo)

    // Checkout
    cy.get('#search', {timeout: 4500})
      .type(itemBarcode)
      .type('{enter}')
    cy.wait(800)

    // Assert checkout
    cy.get(':nth-child(2) > .col > admin-item > .row > :nth-child(1) > a', {timeout: timeOut})
      .should('contain',itemBarcode)
    cy.get(':nth-child(2) > .col > admin-item > .row > :nth-child(4) > .fa', {timeout: timeOut})
      .should('have.class', 'fa-arrow-circle-o-right')

    // Checkin
    cy.get('#search', {timeout: timeOut})
      .type(itemBarcode)
      .type('{enter}')

    // Assert checkin
    cy.get(':nth-child(11) > .col > admin-item > .row > :nth-child(1) > a', {timeout: timeOut})
      .should('contain',itemBarcode)
    cy.get(':nth-child(11) > .col > admin-item > .row > :nth-child(4) > .fa', {timeout: timeOut})
      .should('have.class', 'fa-arrow-circle-o-down')

    // Go back to homepage, search document and delete item
    cy.goToItem(itemBarcode)
    // click on Delete button
    cy.get('#item-' + itemBarcode + '-delete', {timeout: timeOut}).click()
    // Then confirm
    cy.get('.modal-footer > .btn-primary', {timeout: timeOut}).click()
  });
})
