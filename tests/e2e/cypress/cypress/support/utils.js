/* Get current date */
cy.getCurrentDateAndHour = () => {
  return new Date().toISOString().substring(0,16).replace(':', 'H');
};
