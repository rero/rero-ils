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
 * Fill collection editor
 */
Cypress.Commands.add("fillCollectionEditor", (collection) => {
  // Fill in the form
  cy.get('#collection_type').select(collection.collection_type);
  cy.get('#start_date').clear();
  cy.get('#start_date').type(collection.start_date);
  cy.get('body').click(); // Leave datepicker
  cy.get('#end_date').clear();
  cy.get('#end_date').type(collection.end_date);
  cy.get('body').click(); // Leave datepicker
  cy.get('#title').clear();
  cy.get('#title').type(collection.title);
  cy.get('#collection_id').clear();
  cy.get('#collection_id').type(collection.collection_id);
  if (collection.teachers) {
    cy.get('#teachers-0-name').clear();
    cy.get('#teachers-0-name').type(collection.teachers[0].name);
  }
  cy.get('#editor-save-button').click();
});

/**
 * Check collection in detailed view
 */
Cypress.Commands.add("checkCollection", (collection) => {
  cy.get('.d-inline').should('contain', collection.title);
  cy.get('#collection-type').should('contain', collection.collection_type);
  if (collection.teachers) {
    cy.get('#collection #teacher').should('contain', collection.teachers[0].name);
  }
});

