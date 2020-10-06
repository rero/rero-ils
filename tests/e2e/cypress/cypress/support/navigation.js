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
// Go to user profile (using menus). We should be already connected
// tabId: (not mandatory). If exists: go directly to given tabId
Cypress.Commands.add("userProfile", (tabId) => {
  cy.get('#my-account-menu').click()
  cy.get('#my-profile-menu').click()

  // Go to tabId if exist
  if (tabId !== undefined) {
    cy.get('#' + tabId).click()
  }
})

Cypress.Commands.add("goToPublicDocumentDetailView", (itemBarcode) => {
  // Go to homepage
  cy.visit('');
  cy.setLanguageToEnglish();
  // on public context
  cy.get('.d-none > main-search-bar > .flex-grow-1 > .rero-ils-autocomplete > .form-control').clear()
  cy.get('.d-none > main-search-bar > .flex-grow-1 > .rero-ils-autocomplete > .form-control').type(itemBarcode).type('{enter}')
  // Use first element
  cy.get('.card-title > a').click()
})

Cypress.Commands.add("goToProfessionalDocumentDetailView", (itemBarcode) => {
  cy.route('/api/permissions/documents/*').as('getDocumentPermissions');
  // Go to homepage
  cy.get('#homepage-logo').click();
  // on professional context
  cy.get('.form-control').clear();
  cy.get('.form-control').type(itemBarcode).type('{enter}');
  // Use first element
  cy.wait('@getDocumentPermissions');
  cy.get('[name=document-title]').click();
})
