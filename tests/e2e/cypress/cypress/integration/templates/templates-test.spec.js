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

before(function () {
  cy.fixture('users').then(function (userData) {
    this.users = userData;
  });
  cy.fixture('common').then(function (commonData) {
    this.common = commonData;
  });
  cy.fixture('templates').then(function (templateData) {
    this.templates = templateData;
    this.templateName = [this.templates.templateA.name, cy.getCurrentDateAndHour()].join(' ');
  });
});

describe('Templates: Create and use template for a document', function() {

  before('Login as librarian', function() {
    cy.login(this.users.librarians.spock.email, this.common.uniquePwd)
    cy.intercept('GET', '**/professional/records/document**)').as('documentEditor');
    cy.intercept('POST', '/api/templates/').as('createTemplate');
    cy.intercept('GET', '/schemas/documents').as('getDocumentSchemaform');
  });

  after('Delete resources and logout', function() {
    cy.apiDeleteResources('templates', 'name:"' + this.templateName + '"');
    cy.logout();
  });

  it('Create a new template and use it in the editor', function() {
    const template = this.templates.templateA

    // Go to document editor
    cy.visit('/professional/records/documents/new');
    cy.wait('@getDocumentSchemaform');
    // Fill some fields
    // TODO: find how to manage oneOf with Cypress
    // cy.get('#formly_30_enum__0').select(template.document.type[0].main_type);
    // cy.get('#type-0-0-1-2-subtype').select(template.document.type[0].subtype);
    cy.get('#title-0-mainTitle-0-value').type(template.document.title.mainTitle, {force: true});
    // Save as a template
    cy.get('#editor-save-button-split').click();
    cy.get('#editor-save-button-dropdown-split')
      .find('li a.dropdown-item:nth-child(1)')  // TODO: Find a better way to retrieve the correct link to click
      .click();
    // Confirm save
    cy.get('.modal-content #name').type(this.templateName);
    cy.get('.modal-content button:submit').click();
    cy.wait('@createTemplate');
    // Assert that the template was saved
    cy.url().should('include', 'records/templates/detail');

    // Go back to document editor
    cy.visit('/professional/records/documents/new');
    cy.wait('@getDocumentSchemaform');
    // Load template
    cy.get('#editor-load-template-button').click();
    cy.get('.modal-content #template').select(this.templateName);
    cy.get('.modal-content button:submit').click(),
    // Assert that the template was correctly loaded
    // TODO: find how to manage oneOf with Cypress
    // cy.get('#formly_351_enum__0').should('eq', template.document.type[0].main_type);
    // cy.get('#type-0-0-1-3-subtype').should('eq', template.document.type[0].subtype);
    cy.get('#title-0-mainTitle-0-value').should('have.value', template.document.title.mainTitle);
    cy.log('Template loaded successfully !');
  })
})
