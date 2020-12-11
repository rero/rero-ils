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

Cypress.Commands.add("goToPublicDocumentDetailView", (pid, viewcode) => {
  if (viewcode == undefined) {
    cy.visit('/global/documents/' + pid);
  } else {
    cy.visit('/' + viewcode + '/documents/' + pid);
  }
});

Cypress.Commands.add("goToProfessionalDocumentDetailView", (pid) => {
  cy.intercept('/api/permissions/documents/' + pid).as('getPermission');
  cy.visit('/professional/records/documents/detail/' + pid);
  cy.wait('@getPermission');
});

/**
 * Go to item detailed view. Needs to have the item pid stored in '@getItemPid' alias
 *
 * @param itemPid - item pid
 */
Cypress.Commands.add("goToItemDetailView", (pid) => {
    cy.visit('/professional/records/items/detail/' + pid);
});
