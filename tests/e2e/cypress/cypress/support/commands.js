/// <reference types="Cypress" />
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

Cypress.Commands.add('setLanguageToEnglish', () => {
  // Check language and force to given languageCode
  cy.get('#language-menu').then((menu) => {
    menu.click()
    cy.wait(800)
    // Check language and force to English if needed
    cy.get('#help-menu').invoke('text').then((helpmenu) => {
      if (helpmenu == ' Help' || helpmenu == ' Help ') {
        // close Menu (because we're already in english)
        menu.click()
        cy.wait(800)
      }
      else {
        cy.get('#language-menu-en').click()
      }
    })
  })
})

// Setup
Cypress.Commands.add("setup", () => {
  // Set preview size
  cy.viewport(1400, 900)
  // Go to frontpage and hide toolbar
  cy.visit('')

  // Next line is considered as an anti-pattern by cypress as it depends on some specific condition in our application (FLASK_DEBUG=True)
  // Please use `FLASK_DEBUG=False poetry run server` to launch server
  // cy.get('#flHideToolBarButton').click()

  // Check language and force to english
  cy.setLanguageToEnglish()
})

// Logout
Cypress.Commands.add("logout", () => {
  // click on username
  cy.get('#my-account-menu').click()
  // then click on Logout link
  cy.get('#logout-menu').click()
})

Cypress.Commands.add("login", (email, password) => {
  // click on "My account"
  cy.get('#my-account-menu').click()
  cy.get('#login-menu').click()
  cy.get('#email').type(email)
  cy.get('#password').type(password)
  cy.get('form[name="login_user_form"]').submit()
})

// Login to professional interface
Cypress.Commands.add("adminLogin", (email, password) => {
  cy.login(email, password)

  // go to professional interface
  cy.get('#my-account-menu').click()
  cy.get('#professional-interface-menu').click()
  cy.url().should('include', '/professional/')
  // Check language and force to english
  cy.wait(1000)
  cy.get('#language-menu').click()
  cy.setLanguageToEnglish()
 })

// Go to /professional/records/documents (using main menu and click)
Cypress.Commands.add("goToMenu", (menuId) => {
  // Go to professional homepage
  cy.get('.logo').click()
  // Check we're on admin page
  cy.url().should('include', '/professional/')
  // Click on 'menuTitle' from Catalog menu
  cy.get('#' + menuId).click()
})

Cypress.Commands.add("createItem", (barcode, itemType, localisation) => {
  // Go to Catalog > Documents
  cy.goToMenu('documents-menu-frontpage')
  // Use one document (between first and tenth)
  let randomInteger = Math.floor((Math.random() * 9) + 1);
  cy.get(':nth-child(' + randomInteger.toString() + ') > ng-core-record-search-result > admin-documents-brief-view > .card-title > a').click()
  // Click on "Add…" button to add an item
  cy.get('.col > .btn').click()
  // Fill in Item barcode
  cy.get('#formly_9_string_barcode_0').type(barcode)
  // Wait that barcode to be checked (by API)
  cy.wait(800)
  // Fill in Item Call number with barcode content
  cy.get('#formly_9_string_call_number_1').type(barcode)
  // Fill in Item Category
  cy.get('select').first().select(itemType)
  // Fill in localisation (could be 0, 1, etc. to select first element from select list)
  cy.get('select').eq(1).select(localisation)
  
  // Validate the form
  cy.get('.mt-4 > [type="submit"]').click()

  // Assert that the item has been created
  cy.contains(barcode)
})

Cypress.Commands.add("goToItem", (itemBarcode) => {
  // Go to homepage
  if (cy.url().should('include', '/professional/')) {
    // on professional context
    cy.get('.logo').click()
    cy.get('.form-control').type(itemBarcode).type('{enter}')
  }
  else {
    // on public context
    cy.get('#global-logo').click()
    cy.wait(800)
    cy.get('.d-none > main-search-bar > .flex-grow-1 > .rero-ils-autocomplete > .form-control').type(itemBarcode).type('{enter}')
  }
  // Use first element
  cy.get('.card-title > a').click()
})