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
// Go to user profile (using menus)
// tabId: (not mandatory). If exists: go directly to given tabId
Cypress.Commands.add("userProfile", (tabId) => {
  // we should be already connected
  cy.get('#my-account-menu').click()
  cy.get('#my-profile-menu').click()
  cy.wait(2500)
  // Go to tabId if exist
  if (tabId !== undefined) {
    cy.get('#' + tabId).click()
  }
})

// Go to a specific menu from professional homepage
// menuId: `id=` attribute content
Cypress.Commands.add("goToMenu", (menuId) => {
  // Go to professional homepage
  cy.get('#homepage-logo').click()
  // if already on professional, do nothing
  cy.url().then((url) => {
    if (!url.includes('/professional/')) {
      cy.get('#my-account-menu').click()
      cy.get('#professional-interface-menu').click()
      cy.wait(800)
    }
  })

  // Check we're on admin page
  cy.url().should('include', '/professional/')
  // Click on 'menuTitle' from Catalog menu
  cy.get('#' + menuId).click()
})

Cypress.Commands.add("goToItem", (itemBarcode) => {
  // Go to homepage
  cy.get('#homepage-logo').click()
  cy.wait(800)
  cy.url().then((url) => {
    if (url.includes('/professional/')) {
      // on professional context
      cy.get('.form-control').type(itemBarcode).type('{enter}')
    }
    else {
       // on public context
      cy.get('.d-none > main-search-bar > .flex-grow-1 > .rero-ils-autocomplete > .form-control').type(itemBarcode).type('{enter}')
    }
  })
  // Use first element
  cy.get('.card-title > a').click()
})
