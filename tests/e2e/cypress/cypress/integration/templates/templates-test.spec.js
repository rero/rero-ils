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
    this.templateName = this.templates.templateA.name + cy.getCurrentDateAndHour();
  });
});

describe('Templates: Create and use template for a document', function() {

  before('Login as librarian', function() {
    cy.login(this.users.librarians.spock.email, this.common.uniquePwd)
    cy.server();
    cy.route({method: 'GET', url:'/api/templates/?q=*'}).as('api_template_search');
    cy.route({method: 'GET', url:'**/professional/records/document**)'}).as('document_editor');
    cy.route({method: 'POST', url:'/api/templates/'}).as('api_template_create');
  });

  after('Delete resources and logout', function() {
    cy.apiDeleteResources('templates', 'name:"'+this.templateName+'"');
    cy.logout();
  });

  it('Create a new template and use it in the editor', function() {
    const template = this.templates.templateA

    cy.visit('/professional/records/documents/new')
    cy.wait(2000)
    cy.get('ng-core-editor #type').select(template.document.type)
    cy.get('#title-0-mainTitle-0-value').type(template.document.title.mainTitle, {force: true})
    cy.get('#editor-save-button-split').click()
    cy.get('#editor-save-button-dropdown-split')
      .find('li a.dropdown-item:nth-child(1)')  // TODO: Find a better way to retrieve the correct link to click
      .click()
    cy.get('.modal-content #name').type(this.templateName)
    cy.get('.modal-content button:submit').click()
    cy.wait('@api_template_create')
    cy.url().should('include', 'records/templates/detail')

    cy.visit('/professional/records/documents/new')
    cy.wait(2000)
    cy.get('#editor-load-template-button').click()
    cy.wait('@api_template_search')
    cy.get('.modal-content #template').select(this.templateName)
    cy.get('.modal-content button:submit').click()

    cy.url(5000).should('include', '?source=templates&pid=')
    cy.get('ng-core-editor #type').invoke('val').should('eq', template.document.type)
    cy.get('#title-0-mainTitle-0-value').invoke('val').should('eq', template.document.title.mainTitle)
    cy.log('Template loaded successfully !')
  })
})
