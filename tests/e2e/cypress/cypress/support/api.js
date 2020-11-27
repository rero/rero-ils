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

/** API call to create a document ==================================================
  * Create a document
  * :param document - the document to create
  * :param titleSuffix - suffix to append to the title
  */
 Cypress.Commands.add('apiCreateDocument', (document, titleSuffix) => {
  cy.request({
    method: 'POST',
    url: '/api/documents/',
    followRedirect: false,
    body: {
      "type": (document.type).toLowerCase(),
      "title":[{
        "type":"bf:Title",
        "mainTitle":[{
          "value": (document.title.mainTitle + titleSuffix)
        }]
      }],
      "language":[{
        "type":"bf:Language",
        "value": document.languageCode1
      }],
      "provisionActivity":[{
        "statement":[
          {
            "type":"bf:Place",
            "label":[{"value":document.provisionActivity.statement.place}]
          },
          {
            "type":"bf:Agent",
            "label":[{"value":document.provisionActivity.statement.agent}]
          },
          {
            "type":"Date",
            "label":[{"value":document.provisionActivity.statement.date}]
          }
        ],
        "type":"bf:Publication",
        "place":[{
          "type":"bf:Place",
          "country":"xx"
        }],
        "startDate": parseInt(document.provisionActivity.publicationDate1)
      }],
      "issuance":{
        "main_type":"rdami:1001",
        "subtype":"materialUnit"
      }
    }
  })
  .its('body').then((body) => {
    cy.wrap(body.id).as('getDocumentPid');
  })
  .then(() => {
    cy.get('@getDocumentPid').then((pid) => {
      cy.log('Document created, pid = ' + pid);
    });
  });
});


/** API call to create an item ==================================================
  * Create an item
  * :param resourceName - string: the resource type
  * :param query - string: criteria to find items to delete
  */
 Cypress.Commands.add('apiCreateItem', (item, barcode, documentPid, itemTypePid) => {
   let itemTypeRef;
   if (itemTypePid !== undefined) {
     itemTypeRef = 'https://ils.rero.ch/api/item_types/' + itemTypePid;
   } else {
    itemTypeRef = 'https://ils.rero.ch/api/item_types/' + item.itemTypePid
   }
  cy.request({
    method: 'POST',
    url: '/api/items/',
    followRedirect: false,
    body: {
      "acquisition_date":cy.getCurrentDate(),
      "item_type":{
        "$ref":itemTypeRef
      },
      "location":{
        "$ref":('https://ils.rero.ch/api/locations/' + item.locationPid)
      }
      ,"type":"standard",
      "status":"on_shelf"
      ,"barcode":barcode
      ,"call_number":barcode
      ,"document":{
        "$ref":('https://ils.rero.ch/api/documents/' + documentPid)
      }
    }
  })
  .its('body').then((body) => {
    cy.wrap(body.id).as('getItemPid');
  })
  .then(() => {
    cy.get('@getItemPid').then((pid) => {
      cy.log('Item created, pid = ' + pid);
    });
  });
});

/** API call to delete items ==================================================
  * Delete resource items based on a query
  * :param resourceName - string: the resource type
  * :param query - string: criteria to find items to delete
  */
Cypress.Commands.add('apiDeleteResources', (resourceName, query) => {
  const q = encodeURI('/api/'+resourceName+'/?q='+query)
  cy.request(q).its('body.hits.hits', {timeout:2000}).then(hits => {
    hits.forEach(hit => {
      const pid = hit.metadata.pid
      cy.request({
        method: 'DELETE',
        url: (['/api', resourceName, pid].join('/'))
      })
      cy.log([resourceName, '#' + pid, 'deleted'].join(' '))
    })
  })
});

/** API call to create an item type ==================================================
  * Create an item type
  * :param itemType - the item type to create
  * :param nameSuffix - suffix to append to the name
  */
 Cypress.Commands.add('apiCreateItemType', (itemType, nameSuffix) => {
 cy.request({
   method: 'POST',
   url: '/api/item_types/',
   followRedirect: false,
   body: {
    "type": itemType.type,
    "name": (itemType.name + nameSuffix),
    "description": itemType.description,
    "organisation": {
      "$ref":('https://ils.rero.ch/api/organisations/' + itemType.organisation_pid)
    }
  }
 })
 .its('body').then((body) => {
   cy.wrap(body.id).as('getItemTypePid');
 })
 .then(() => {
   cy.get('@getItemTypePid').then((pid) => {
     cy.log('Item type created, pid = ' + pid);
   });
 });
});

/** API call to create a patron type ==================================================
  * Create patron type
  * :param patronType - the patron type to create
  * :param nameSuffix - suffix to append to the name
  */
 Cypress.Commands.add('apiCreatePatronType', (patronType, nameSuffix) => {
  cy.request({
    method: 'POST',
    url: '/api/patron_types/',
    followRedirect: false,
    body: {
      "name": (patronType.name + nameSuffix),
      "description": patronType.description,
      "organisation":{
        "$ref": ('https://ils.rero.ch/api/organisations/' + patronType.organisation_pid)
      }
    }
  })
  .its('body').then((body) => {
    cy.wrap(body.id).as('getPatronTypePid');
  })
  .then(() => {
    cy.get('@getPatronTypePid').then((pid) => {
      cy.log('Patron type created, pid = ' + pid);
    });
  });
});

 /** API call to create a patron ==================================================
  * Create patron
  * :param patron - the patron to create
  * :param patronTypePid - patron type pid
  */
 Cypress.Commands.add('apiCreatePatron', (patron, patronTypePid) => {
  cy.request({
    method: 'POST',
    url: '/api/patrons/',
    followRedirect: false,
    body: {
      "patron": {
        "expiration_date": patron.patron.expiration_date,
        "type": {
          "$ref":('https://ils.rero.ch/api/patron_types/' + patronTypePid)
        },
        "barcode": patron.patron.barcode,
        "communication_channel": patron.patron.communication_channel,
        "communication_language": patron.patron.communication_language
      },
      "roles": patron.roles,
      "first_name": patron.first_name,
      "last_name": patron.last_name,
      "birth_date": patron.birth_date,
      "username": patron.username,
      "email": patron.email
    }
  })
  .its('body').then((body) => {
    cy.wrap(body.id).as('getPatronPid');
  })
  .then(() => {
    cy.get('@getPatronPid').then((pid) => {
      cy.log('Patron created, pid = ' + pid);
    });
  });
});

/** API call to update a patron ==================================================
  * Update patron
  * :param patron - the patron to update
  * :param patronTypePid - patron type pid
  */
 Cypress.Commands.add('apiUpdatePatron', (patron, patronTypePid) => {
  cy.request({
    method: 'PUT',
    url: '/api/patrons/' + patron.pid,
    followRedirect: false,
    body: {
      "patron": {
        "barcode": patron.patron.barcode,
        "communication_channel": patron.patron.communication_channel,
        "communication_language": patron.patron.communication_language,
        "expiration_date": patron.patron.expiration_date,
        "type": {
          "$ref": ('https://ils.rero.ch/api/patron_types/' + patronTypePid)
        }
      },
      "$schema":"https://ils.rero.ch/schemas/patrons/patron-v0.0.1.json",
      "birth_date": patron.birth_date,
      "city": patron.city,
      "email": patron.email,
      "first_name": patron.first_name,
      "last_name": patron.last_name,
      "phone": patron.phone,
      "pid": patron.pid,
      "postal_code": patron.postal_code,
      "roles": patron.roles,
      "street": patron.street,
      "user_id": patron.user_id,
      "username": patron.username
    }
  })
  .its('body').then((body) => {
    cy.wrap(body.id).as('getPatronPid');
  })
  .then(() => {
    cy.get('@getPatronPid').then((pid) => {
      cy.log('Patron updated, pid = ' + pid);
    });
  });
});
