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

describe('Scenario A (standard loan)', function () {
  // DESCRIPTION
  // ===========
  // A request is made on on-shelf item, that has no requests,
  // to be picked up at the owning library.
  // Validated by the librarian.
  // Picked up at same owning library.
  // And returned on-time at the owning library.

  // Pull data from common.json and users.json
  beforeEach(function () {
    // get users
    cy.fixture('users').then(function (userData) {
      this.users = userData;
    })
    // get common data
    cy.fixture('common').then(function (commonData) {
      this.common = commonData;
    })
    // setup application: Use a specific preview size, specific language
    cy.setup()
  })

  // Create a barcode using current date
  let currentDate = cy.getCurrentDateAndHour()
  var barcode = currentDate + '_scenarioA'
  it('Creates a new item from professional UI', function() {
    // needed variables
    const password = this.common.uniquePwd;
    const virgile = this.users.librarians.virgile;

    // Login as admin
    cy.adminLogin(virgile.email, password)

    // Create a new item
    cy.createItem(barcode, 'Standard', 'Espaces publics')

    // Check barcode exists
    cy.get('#item-' + barcode).should('contain', barcode)

    cy.logout()
  }),
  it('Makes a request on on-shelf item', function() {
    // used variables
    const password = this.common.uniquePwd;
    const simonetta = this.users.patrons.simonetta;
    const locationCode = 'AOSTE-LYCEE-PUB';

    // Login as normal user to request an item
    cy.login(simonetta.email, password)

    // Search previous item
    cy.wait(1000)
    cy.goToItem(barcode)

    // Use 'request' button and choose first item from dropdown list
    cy.get('#' + barcode + '-dropdownMenu').click()
    // Click on selected pickup location (force because menu can go over browser view)
    cy.get('#' + locationCode).click({force: true})

    // Go to user profile, directly on requests-tab
    cy.userProfile('requests-tab')
    // Check barcode exists and that it's requested
    cy.get('#item-' + barcode).should('contain', barcode)

    cy.logout()
  }),
  it('Validates Simonetta\'s request', function () {
    // used variables
    const password = this.common.uniquePwd;
    const simonetta = this.users.patrons.simonetta;
    const virgile = this.users.librarians.virgile;

    // Login as librarian to validate user request
    cy.login(virgile.email, password)
 
    // Go to requests list to search pending request with its barcode
    cy.goToMenu('requests-menu-frontpage')
    cy.wait(3000)
    // Check document exists in table
    cy.get('table').should('contain', barcode)
    // Enter the barcode and validate with ENTER
    cy.get('#search').type(barcode).type('{enter}')

    // the item should be now available to be picked-up (in user profile)
    // Go to patrons list
    cy.goToMenu('patrons-menu-frontpage')
    // Search simonetta with its name and validate with ENTER
    cy.get('#search').type(simonetta.name).type('{enter}')
    // Wait the search result to be displayed
    cy.wait(4000)
    // Select first user and its link
    cy.get('.ml-3 > a > span').click()
    // Click on tab called "To pick up"
    cy.get('#pick-up-tab').click()
    // The item should be present
    cy.get('.content').should('contain', barcode)

    cy.logout()

  }),
  it('Librarian registers Simonetta\'s pickup', function () {
    const password = this.common.uniquePwd;
    const simonetta = this.users.patrons.simonetta;
    const virgile = this.users.librarians.virgile;

    // Login as librarian to validate user request
    cy.login(virgile.email, password)

    // Go to circulation search bar
    cy.goToMenu('circulation-menu-frontpage')
    // Enter Simonetta's barcode (to get its profile)
    cy.get('#search').type(simonetta.barcode).type('{enter}')
    cy.wait(8000) // wait a lot because this tab is a time hell
    // Insert barcode
    cy.get('#search').type(barcode).type('{enter}')
    cy.wait(2500)
    // Item barcode should be present
    cy.get('#item-' + barcode).should('contain', barcode)

    cy.logout()
  }),
  it('Some times after that, the librarian registers the return of the item', function () {
    const password = this.common.uniquePwd;
    const simonetta = this.users.patrons.simonetta;
    const virgile = this.users.librarians.virgile;

    // Login as librarian to validate user request
    cy.login(virgile.email, password)

    // Go to circulation search bar
    cy.goToMenu('circulation-menu-frontpage')
    // Enter item barcode
    cy.get('#search').type(barcode).type('{enter}')
    cy.wait(8000)
    // Item barcode should be present in the list
    cy.get('#item-' + barcode).should('contain', barcode)
    cy.get('#item-' + barcode).should('contain', 'on shelf')
    cy.get('#item-' + barcode).should('contain', 'checked in')
  })

  // WHAT you always have to do in tests:
  // 1) set up the application state
  // 2) take an action
  // 3) make an assertion
})
