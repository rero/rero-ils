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
  cy.fixture('order').then(function (orderData) {
    this.order = orderData;
  });
  cy.fixture('users').then(function (userData) {
    this.users = userData;
  });
  cy.fixture('common').then(function (commonData) {
    this.common = commonData;
  });
})

describe('Acquisition - Order', function() {
  it('Create-Delete an order', function() {
    const order = this.order.order;
    let total_amount = 0;

    cy.setup()
    cy.adminLogin(this.users.librarians.virgile.email, this.common.uniquePwd);

    // Go to Orders Menu
    cy.goToMenu('orders-menu-frontpage')

    // Click on "Add" to create a new order
    cy.get('.btn-primary').click()
    cy.wait(800)

    // Fill in the form (Order Header)
    // Put some wait() command to slowdown the screen display
    cy.get('#vendor-\\$ref').select(order.vendor_reference)
    cy.get('#order_number').type(order.order_number)
    cy.wait(800)
    cy.get('#order_status').select(order.order_status)
    // Enter the order date
    cy.get('#order_date').type(order.order_date)
    // click to put the focus and disable the calendar display
    cy.get('#order_date').click()
    cy.get('#description').type(order.description)
    // Save
    cy.get('.btn-primary').click()
    cy.wait(3000)

     // Assert that the order has been created
     cy.get('admin-acquisition-order-detail-view.ng-star-inserted > .mb-3').should('contain',order.order_number)

    // create order line 1
    cy.populateOrderLine(order.order_number,
      order.lines[0].acq_account_reference,
      order.lines[0].document_reference,
      order.lines[0].order_line_status,
      order.lines[0].amount,
      order.lines[0].note)

    // Update total amount
    total_amount += order.lines[0].amount

    // create order line 2
    cy.populateOrderLine(order.order_number,
      order.lines[1].acq_account_reference,
      order.lines[1].document_reference,
      order.lines[1].order_line_status,
      order.lines[1].amount,
      order.lines[1].note)

      // Update total amount
    total_amount += order.lines[1].amount

    // create order line 3
    cy.populateOrderLine(order.order_number,
      order.lines[2].acq_account_reference,
      order.lines[2].document_reference,
      order.lines[2].order_line_status,
      order.lines[2].amount,
      order.lines[2].note)

    total_amount += order.lines[2].amount

    // Wait the display of all infos on the page
    cy.wait(4000)

    // Assert that the lines have been created
    // check that the total amount (sum of 3 lines) is correct
    cy.get('.row > :nth-child(12)').should('contain', total_amount)

    // Delete 3 order lines
    // wait 5 sec between each to allow correct screen rendering
    cy.get(':nth-child(2) > .row > .p-0 > .btn-outline-danger > .fa').click()
    cy.get('#modal-confirm-button').click()
    cy.wait(5000)
    cy.get(':nth-child(2) > .row > .p-0 > .btn-outline-danger > .fa').click()
    cy.get('#modal-confirm-button').click()
    cy.wait(5000)
    cy.get(':nth-child(2) > .row > .p-0 > .btn-outline-danger > .fa').click()
    cy.get('#modal-confirm-button').click()
    cy.wait(5000)

    // Go to Orders Menu
    cy.goToMenu('orders-menu-frontpage')

    // Delete order
    cy.get('admin-acquisition-order-brief-view.ng-star-inserted > .mb-0 > a').contains('Cypress-Order-123456').click()
    cy.get('#detail-delete-button').click()
    cy.get('#modal-confirm-button').click()
    cy.wait(2000)

     // Assert that the order has been deleted
     cy.contains(order.order_number).should('not.exist')

  });
})
