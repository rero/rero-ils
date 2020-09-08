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
// Scan the patron barcode, then the item barcode (this does a checkout)
Cypress.Commands.add('scanPatronBarcodeThenItemBarcode', (patron, itemBarcode) => {
  // Enter patron barcode
  cy.get('#search').type(patron.barcode).type('{enter}');
  // Assert that patron info is displayed
  cy.get('#patron-last-name').should('contain', patron.last_name);
  cy.get('#patron-first-name').should('contain', ', ' + patron.first_name);
  // Enter item barcode for checkout
  cy.get('#search').type(itemBarcode).type('{enter}');
});

// Scan the barcode of an item (this can do a checkin, a receive or "nothing", depending on context)
Cypress.Commands.add('scanItemBarcode', (itemBarcode) => {
  // Enter item barcode for checkout
  cy.get('#search').type(itemBarcode).type('{enter}');
});
