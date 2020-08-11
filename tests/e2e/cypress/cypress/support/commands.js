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
//#endregion

//#region Document editor ----------------------------------------------------->
Cypress.Commands.add("populateSimpleRecord", (document) => {
  cy.fixture('document').then(function (documentData) {
    this.document = documentData;
  });
  // Choose type
  cy.get('ng-core-editor-select-with-sort-type.ng-star-inserted > #type', {timeOut: 10000}).select(document.type);

  // Enter title
  cy.get('#title-0-mainTitle-0-value').type(document.title.mainTitle);

  // Enter provision activity
  cy.get('#provisionActivity-0-type').select(document.provisionActivity.type);
  cy.get('#provisionActivity-0-startDate').type(document.provisionActivity.publicationDate1);
  cy.get('#provisionActivity-0-statement-0-label-0-value').type(document.provisionActivity.statement.place);
  cy.get('#provisionActivity-0-statement-1-label-0-value').type(document.provisionActivity.statement.agent);
  cy.get('#provisionActivity-0-statement-2-label-0-value').type(document.provisionActivity.statement.date);

  // Choose language
  cy.get('#language-0-value').select(document.language1);

  // Choose mode of issuance
  // TODO find a way to use custom id for main type select
  cy.get('#formly_163_enum__0').select(document.issuance.issuanceMainType);
  cy.get('[style=""] > ng-core-editor-formly-object-type.ng-star-inserted > .row > #field-issuance-subtype > .content > :nth-child(1) > formly-field > ng-core-horizontal-wrapper.ng-star-inserted > .form-group > .d-flex > .flex-grow-1 > formly-field-select.ng-star-inserted > #issuance-subtype').select(document.issuance.issuanceSubtype);
});

Cypress.Commands.add("saveRecord", () => {
  // Assert save button is active
  cy.get('#editor-save-button').should('not.be.disabled');

  // Save document (redirection to detail document view)
  cy.get('#editor-save-button').click();
});

Cypress.Commands.add("checkDocumentEssentialFields", (document) => {
  cy.fixture('document').then(function (documentData) {
    this.document = documentData;
  });
  cy.get('#doc-language-0').should('contain', document.language1);
  cy.get('#doc-issuance').should('contain', document.issuance.issuanceMainTypeCode + ' / monographicSeries');
  cy.get('#doc-title').should('contain', document.title.mainTitle);
  cy.get('#doc-provision-activity-0').should('contain', document.provisionActivity.statement.place + ' : ' + document.provisionActivity.statement.agent + ', ' + document.provisionActivity.statement.date);
});
//#endregion ------------------------------------------------------------------>
