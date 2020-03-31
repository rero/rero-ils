/*
 * RERO ILS UI
 * Copyright (C) 2019 RERO
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, version 3 of the License.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

describe('Frontpage', function() {
  it('Visits the frontpage', function() {

    // const domain = Cypress.baseUrl()
    const patronBarcode= '2050124311'
    const itemBarcode = '10000000085'

    // Viewport
    cy.viewport(1400, 900)

    // Check frontpage
    cy.visit('')
    cy.contains('Get into your library')
    cy.get('#flHideToolBarButton').click()

    // Login
    cy.visit('/professional')
    cy.get('#email').type('reroilstest+virgile@gmail.com')
    cy.get('#password').type('123456')
    cy.get('form[name="login_user_form"]').submit()

    // Go to Circulation
    cy.contains('Prêt').click()

    // Enter a patron barcode
    cy.get('#search')
      .type(patronBarcode)
      .type('{enter}')

    // Assert that patron info is displayed
    cy.contains('Casalini, Simonetta')

    // Checkout
    cy.get('#search', {timeout: 10000})
      .type(itemBarcode)
      .type('{enter}')

    // Assert checkout
    cy.get('html')
      .find('.fa-arrow-circle-o-right', {timeout: 10000})

    // Checkin
    cy.get('#search')
    .type(itemBarcode)
    .type('{enter}')

    // Assert checkin
    cy.get('html')
      .find('.fa-arrow-circle-o-down', {timeout: 10000})

  })
})
