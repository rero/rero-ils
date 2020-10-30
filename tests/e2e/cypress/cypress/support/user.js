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

Cypress.Commands.add("logout", () => {
  cy.visit('/signout');
  cy.get('body').should('contain', 'My account');
});

Cypress.Commands.add("login", (email, password) => {
  cy.request({
    method: 'POST',
    url: '/api/login',
    followRedirect: false,
    body: {
      'email': email,
      'password': password
    }
  }).then(() => {
    cy.visit('/lang/en'); // this forces the language to english and preserves it even while using cy.visit
    cy.get('body').should('contain', 'RERO ID');
  });
});

// Login to professional interface
Cypress.Commands.add("adminLogin", (email, password) => {
  cy.login(email, password);
  cy.visit('/professional');
  cy.get('body').should('contain', 'RERO ILS administration');
});
