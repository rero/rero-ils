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
  // Fill in the form
  cy.get('#barcode').type(barcode)
  cy.get('#call_number').type(barcode)
  // Select item type
  cy.get('select').first().select(item.itemTypeUri)
  // Select location
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

Cypress.Commands.add("populateSimpleRecord", (document) => {
  // Choose type
  if (document.hasOwnProperty('type')) {
    cy.get('ng-core-editor-select-with-sort-type.ng-star-inserted > #type').select(document.type);
  }
  // Enter title
  if (document.hasOwnProperty('title')) {
    if (document.title.hasOwnProperty('mainTitle')) {
      cy.get('#title-0-mainTitle-0-value').type(document.title.mainTitle);
    }
  }
  // Enter provision activity
  if (document.hasOwnProperty('provisionActivity')) {
    cy.get('#provisionActivity-0-type').select(document.provisionActivity.type);
    cy.get('#provisionActivity-0-startDate').type(document.provisionActivity.publicationDate1);
    cy.get('#provisionActivity-0-statement-0-label-0-value').type(document.provisionActivity.statement.place);
    cy.get('#provisionActivity-0-statement-1-label-0-value').type(document.provisionActivity.statement.agent);
    cy.get('#provisionActivity-0-statement-2-label-0-value').type(document.provisionActivity.statement.date);
  }
  // Choose language
  if (document.hasOwnProperty('language1')) {
    cy.get('#language-0-value').select(document.language1);
  }
  // Choose mode of issuance
  // TODO find a way to use custom id for oneOf
});

Cypress.Commands.add("saveRecord", () => {
  // Assert save button is active
  cy.get('#editor-save-button').should('not.be.disabled');

  // Save document (redirection to detail document view)
  cy.get('#editor-save-button').click();
});

Cypress.Commands.add("checkDocumentEssentialFields", (document) => {
  cy.fixture('documents').then(function (documents) {
    this.documents = documents;
  });
  cy.get('#doc-language-0').should('contain', document.language1);
  cy.get('#doc-issuance').should('contain', document.issuance.mainTypeCode + ' / materialUnit');
  cy.get('#doc-title').should('contain', document.title.mainTitle);
  cy.get('#doc-provision-activity-0').should('contain', document.provisionActivity.statement.place + ' : ' + document.provisionActivity.statement.agent + ', ' + document.provisionActivity.statement.date);
});
