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

/**
 * Get current date and hour
 * Output example: 2020-11-30T15H26
*/
cy.getCurrentDateAndHour = () => {
  return new Date().toISOString().substring(0,16).replace(':', 'H');
};

/**
 * Get current date
 * Output example: 2020-11-30
*/
cy.getCurrentDate = () => {
  return cy.getCurrentDateAndHour().substring(0,10);
};

/**
 * Get date displayed (translated)
 * Output example for US-en: 12/30/20 or 1/1/20
*/
cy.getDateDisplayed = (date, locale, separator) => {
  let dateInfo = [];
  const year = date.substring(2, 4);
  let month = date.substring(5, 7);
  let day = date.substring(8, 10);
  if (parseInt(month) < 10) {
    month = month.substring(1,2);
  }
  if (parseInt(day) < 10) {
    day = day.substring(1,2);
  }
  switch(locale) {
    case 'fr':
      dateInfo = [day, month, year];
      break;
    default:
      dateInfo = [month, day, year];
  }
  return dateInfo.join(separator);
};
