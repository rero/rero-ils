# Developer resources

This directory contains resources about RERO ILS: loan state chart, item state chart,
link between RERO resources chart, list of circulation actions, etc.

## RERO ILS resources chart

A chart with some RERO ILS resources: Patron, Document, Item and Budget.

To generate the chart:

```bash
make
```

`reroils_resources.png` and `reroils_resources.svg` will be generated.

## Circulation

- [actions](./circulation/actions.md): detail of all actions in the circulation module
- [scenarios](./circulation/scenarios.md): use previous actions to compose more complex scenarios

### Loan state chart

A chart with all loan states. Can be found in the **circulation** directory.

To generate the chart:

```bash
cd circulation && make
```

`loan_states.png` and `loan_states.svg` will be generated.
