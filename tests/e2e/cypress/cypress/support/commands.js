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

//#region User
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
  cy.wait(1000)

  // set language to english BEFORE going to professional interface
  cy.setLanguageToEnglish()

  // go to professional interface
  cy.get('#my-account-menu').click()
  cy.get('#professional-interface-menu').click()
  cy.url().should('include', '/professional/')
 })
 //#endregion

 //#region Navigation
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
//#endregion

//#region Record
Cypress.Commands.add("createItem", (barcode, itemType, localisation) => {
  // Go to Catalog > Documents
  cy.goToMenu('documents-menu-frontpage')
  // Use one document (between first and tenth)
  let randomInteger = Math.floor((Math.random() * 9) + 1);
  cy.wait(2100) // because ngx-spinner hide the menu with a black transparent filter
  cy.get(':nth-child(' + randomInteger.toString() + ') > ng-core-record-search-result > admin-documents-brief-view > .card-title > a').click()
  // Click on "Add…" button to add an item
  cy.get('.col > .btn').click()
  // Fill in Item barcode
  cy.get('#barcode').type(barcode)
  // Wait that barcode to be checked (by API)
  cy.wait(800)
  // Fill in Item Call number with barcode content
  cy.get('#call_number').type(barcode)
  // Fill in Item Category
  cy.get('select').first().select(itemType)
  // Fill in localisation (could be 0, 1, etc. to select first element from select list)
  cy.get('select').eq(1).select(localisation)

  // Validate the form
  cy.get('.mt-4 > [type="submit"]').click()

  // Assert that the item has been created
  cy.contains(barcode, {timeout: 8000})
})
//#endregion

Cypress.Commands.add("deleteRecordFromDetailView", () => {
  // Delete record and confirm deletion
  cy.get('#detail-delete-button').click();
  cy.get('#modal-confirm-button').click();
});

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
