// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
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

// Setup
Cypress.Commands.add("setup", () => {
  // Set preview size
  cy.viewport(1400, 900)
  // Go to frontpage and hide toolbar
  cy.visit('')
  cy.get('#flHideToolBarButton').click()
  // Check language and force to english if needed
  cy.get('header h1').invoke('text').then((text) => {
    if (text !== 'Get into your library') {
      cy.contains('Menu').click()
      cy.contains('English').click()
    }
  })
})

// Login to professional interface
Cypress.Commands.add("adminLogin", (email, password) => {
  cy.visit('/professional')
  cy.get('#email').type(email)
  cy.get('#password').type(password)
  cy.get('form[name="login_user_form"]').submit()
  // Check language and force to english if needed
  cy.get('ng-core-menu a').contains('Menu').click()
  cy.get('ng-core-menu .dropdown-item').first().click()
 })
