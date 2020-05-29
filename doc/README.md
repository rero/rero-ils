# Developer resources

This directory should contain resources about RERO-ils as Loan state chart, Item state chart, Link between RERO resources chart, list of circulation actions, etc.

# RERO-ils resources chart

This is a chart with some RERO-ils resources as Patron, Document, Item and Budget.

To generate the chart:

```bash
make
```

**reroils\_resources.png** and **reroils\_resources.svg** should be generated.

# Circulation

  * [actions](./circulation/actions.md): detail of all actions in circulation module
  * [scenarios](./circulation/scenarios.md): use previous actions to compose more complex scenarios

## Loan state chart

A chart with all Loan states.

Can be found in **circulation** directory.

To generate the chart:

```
cd circulation && make loan_states
```

**loan\_states.png** and **loan\_states.jpg** should be generated.

