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

/**
 * Create an item in document detail view
 */
Cypress.Commands.add("createItemFromDocumentDetailView", (barcode, item) => {
  // Click on "Add…" button to add an item
  cy.get('.col > .btn').click()
  // Fill in Item barcode
  cy.get('#barcode').type(barcode)
  // Fill in Item Call number with barcode content
  cy.get('#call_number').type(barcode)
  // Fill in Item Category
  cy.get('select').first().select(item.itemTypeUri)
  // Fill in localisation (could be 0, 1, etc. to select first element from select list)
  cy.get('select').eq(1).select(item.location)
  // Submit form
  cy.get('.mt-4 > [type="submit"]').click()
  // Assert that the item has been created
  cy.get('.main-content').should('contain', barcode)
})

Cypress.Commands.add("deleteRecordFromDetailView", () => {
  // Delete record and confirm deletion
  cy.get('#detail-delete-button').click();
  cy.get('#modal-confirm-button').click();
});
