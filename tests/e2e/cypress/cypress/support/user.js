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
// Logout
Cypress.Commands.add("logout", () => {
  // click on username
  cy.get('#my-account-menu').click()
  // then click on Logout link
  cy.get('#logout-menu').click()
})

Cypress.Commands.add("login", (email, password) => {
  // click on "My account"
  cy.get('#my-account-menu').click()
  cy.get('#login-menu').click()
  cy.get('#email').type(email)
  cy.get('#password').type(password)
  cy.get('form[name="login_user_form"]').submit()
})

// Login to professional interface
Cypress.Commands.add("adminLogin", (email, password) => {
  cy.login(email, password)
  // set language to english BEFORE going to professional interface
  cy.setLanguageToEnglish()
  // go to professional interface
  cy.get('#my-account-menu').click()
  cy.get('#professional-interface-menu').click()
  cy.url(60000).should('include', '/professional/')
 })
