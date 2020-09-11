/// <reference types="Cypress" />
// ***********************************************
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add("login", (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add("drag", { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add("dismiss", { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite("visit", (originalFn, url, options) => { ... })

//#region Utils
Cypress.Commands.add('setLanguageToEnglish', () => {
  // Check language and force to given languageCode
  cy.get('#language-menu').then((menu) => {
    menu.click()
    // Check language and force to English if needed
    cy.get('#help-menu').invoke('text').then((helpmenu) => {
      if (helpmenu == ' Help') {
        // close Menu (because we're already in english)
        menu.click()
      }
      else {
        cy.get('#language-menu-en').click({force: true})
      }
    })
  })
  // Wait for the menu to close
  // TODO: find a better way (same as logout command)
  cy.wait(1000)
})
