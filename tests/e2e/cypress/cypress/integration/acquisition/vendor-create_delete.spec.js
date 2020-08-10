/// <reference types="Cypress" />
/*

RERO ILS
Copyright (C) 2020 RERO
Copyright (C) 2020 UCLouvain

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
  cy.fixture('vendor').then(function (vendorData) {
    this.vendor = vendorData;
  });
  cy.fixture('users').then(function (userData) {
    this.users = userData;
  });
  cy.fixture('common').then(function (commonData) {
    this.common = commonData;
  });
})

describe('Acquisition - Vendor', function() {
  it('Create-Delete a vendor', function() {
    const vendor = this.vendor.vendor;

    cy.setup()
    cy.adminLogin(this.users.librarians.virgile.email, this.common.uniquePwd);

    // Go to Budgets Screen
    cy.goToMenu('vendors-menu-frontpage');

    // Click on "Add" button to create a new vendor
    cy.get('#search-add-button').click()
    cy.wait(800)

    // Fill in the account Name
    cy.get('#name').type(vendor.name)
    cy.get('#website').type(vendor.website)
    cy.get('#note').type(vendor.note)
    cy.get('#vat_rate').type(vendor.vat_rate)
    cy.get('#default_contact-contact_person').type(vendor.default_contact_contact_person)
    cy.get('#default_contact-street').type(vendor.default_contact_street)
    cy.get('#default_contact-postal_code').type(vendor.default_contact_postal_code)
    cy.get('#default_contact-city').type(vendor.default_contact_city)
    cy.get('#default_contact-country').type(vendor.default_contact_country)
    cy.get('#default_contact-phone').type(vendor.default_contact_phone)
    cy.get('#default_contact-email').type(vendor.default_contact_email)

    cy.get('#order_contact-contact_person').type(vendor.order_contact_contact_person)
    cy.get('#order_contact-street').type(vendor.order_contact_street)
    cy.get('#order_contact-postal_code').type(vendor.order_contact_postal_code)
    cy.get('#order_contact-city').type(vendor.order_contact_city)
    cy.get('#order_contact-country').type(vendor.order_contact_country)
    cy.get('#order_contact-phone').type(vendor.order_contact_phone)
    cy.get('#order_contact-email').type(vendor.order_contact_email)

    cy.wait(800)
    cy.get('#editor-save-button').click()
    cy.wait(4000)

    // Assert that the values are correctly displayed
    cy.get('admin-vendor-detail-view.ng-star-inserted > .mb-3').should('contain',vendor.name)

    // click on Contact Tab
    cy.get('#order_address-link > span').click()
    // Assert that the values are correctly displayed
    cy.get('#order_address > admin-address-type > article > .m-2 > :nth-child(1) > .row > :nth-child(2)').should('contain',vendor.order_contact_contact_person)
    cy.wait(800)

    // click on Default Tab
    cy.get('#default_address-link > span').click()
    // Assert that the values are correctly displayed
    cy.get('#default_address > admin-address-type > article > .m-2 > :nth-child(1) > .row > :nth-child(2)').should('contain',vendor.default_contact_contact_person)
    cy.wait(800)

    // Delete the vendor
    cy.get('#detail-delete-button').click()
    cy.wait(800)
    cy.get('#modal-confirm-button').click()
    cy.wait(3000)
  });
})
