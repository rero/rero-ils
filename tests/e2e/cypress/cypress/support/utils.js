/* Get current date */
cy.getCurrentDateAndHour = () => {
  return new Date().toISOString().substring(0,16).replace(':', 'H');
};

cy.getCurrentDate = () => {
  return cy.getCurrentDateAndHour().substring(0,10);
};
