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
    const timeOut = 30000;

    cy.setup()
    cy.adminLogin(librarianEmail, librarianPwd)

    // Go to the detailed view of a document
    cy.visit(documentUrl, { timeout: timeOut })

    // Create an item
    cy.get('.col > .btn',{timeout: timeOut}).click()
    cy.get('#formly_6_string_barcode_0').type(itemBarcode)
    cy.wait(3000)
    cy.get('#formly_6_string_call_number_1').type(itemBarcode)
    cy.get('select').first().select('Standard')
    cy.get('select').eq(1).select('Espaces publics')
    cy.get('.mt-4 > [type="submit"]').click()

    // Assert that the item has been created
    cy.get(':nth-child(3) > .card > .card-body > .mt-1 > .offset-sm-1 > a', {timeout: timeOut})
      .should('contain',itemBarcode)

    // Go to Circulation
    cy.visit(circUrl, { timeout: timeOut })

    // Enter a patron barcode
    cy.get('#search', {timeout: timeOut})
      .type(patronBarcode)
      .type('{enter}')

    // Assert that patron info is displayed
    cy.get(':nth-child(2) > :nth-child(1) > .col-md-10', {timeout: timeOut})
      .should('contain', patronInfo)

    // Checkout
    cy.get('#search', {timeout: timeOut})
      .type(itemBarcode)
      .type('{enter}')

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

    // Go back to document detailed view and delete item
    cy.visit(documentUrl, { timeout: timeOut })
    cy.get(':nth-child(3) > .card > .card-body > .mt-1 > .col-sm-4 > .btn-outline-danger', {timeout: timeOut}).click()
    cy.get('.modal-footer > .btn-primary', {timeout: timeOut}).click()
  });
})
