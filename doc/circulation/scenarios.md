# Circulation Scenarios

## Template

Short description of the scenario.

```text
action_1  [action parameters or notes]
action_2  [action parameters or notes]
action_3  [action parameters or notes]
```

## scenario_A (standard loan)

:heavy_check_mark:

A request is made on an on-shelf item with no existing requests, to be picked up at the
owning library. Validated by the librarian. Picked up at the owning library and returned
on time at the owning library.

```text
ADD_REQUEST_1.1  [item, pickup_library, patron]
VALIDATE_1.2     [librarian, transaction_library, loan]
CHECKOUT_2.1     [librarian, transaction_library, loan]
CHECKIN_3.1.1    [librarian, transaction_library, loan]
```

## scenario_B (standard loan with transit)

:heavy_check_mark:

A request is made on an item of library A, on-shelf without previous requests, to be
picked up at library B. Validated by librarian A and goes in transit. Received by
librarian B and goes to desk. Picked up at library B. Returned on time at library B,
goes in transit. Received at library A and goes on shelf.

```text
ADD_REQUEST_1.1
VALIDATE_1.2
CHECKIN_4.1
CHECKOUT_2.1
CHECKIN_3.1.2
CHECKIN_5.1.1
```

## scenario_C (item with multiple in-transit requests)

:heavy_check_mark:

A request is made on an item of library A, on-shelf without previous requests, to be
picked up at library B. Validated by librarian A and goes in transit. Received by
librarian B and goes to desk. Picked up at library B. Requested by patron_2 to be picked
up at library C. Returned on time at library B, goes in transit to library C. Received
at library C and goes to desk. Picked up at library C by patron_2. Renewed by patron_2.
Returned on time at library C after the end of the first renewal, goes in transit to
library A. Received at library A and goes on shelf.

```text
ADD_REQUEST_1.1
VALIDATE_1.2
CHECKIN_4.1
CHECKOUT_2.1
ADD_REQUEST_3.2.1
CHECKIN_3.2.2.2
CHECKIN_4.1
CHECKOUT_2.1
EXTEND_3.1
CHECKIN_3.1.2
CHECKIN_5.1.1
```

## scenario_D (denied actions and unconventional workflow)

:heavy_check_mark:

An inexperienced librarian A (library A) makes a checkin on item A, which is on shelf at
library A and without requests (→ nothing happens). Item A is requested by patron A.
Another librarian B of library B tries to check it out for patron B (→ denied). The item
is requested by patron B with pickup at library B. Librarian B tries again to check it
out for patron B (→ denied), then for patron A (→ ok). Patron A tries to renew item A
(→ denied). Patron A returns item A at library B. The item is at desk for patron B.

Patron A requests it again, with pickup at library A. Unexpectedly, librarian A tries to
check out item A for patron A (→ denied). He then checks it out for patron B. Patron B
returns item A at library C. It goes in transit to library A for patron A.

Before arriving to library A, it transits through library B. Patron A cancels his
request. Item A transits through library C. It is then received at its owning library A.

```text
CHECKIN_1.1.1
ADD_REQUEST_1.1
CHECKOUT_1.2.2
ADD_REQUEST_1.2.2
CHECKOUT_1.2.2
CHECKOUT_1.2.1
EXTEND_3.2
CHECKIN_3.2.1
ADD_REQUEST_2.2
CHECKOUT_2.2
CHECKOUT_2.1
CHECKIN_3.2.2.1
CHECKIN_5.2.2.1
CANCEL_REQUEST_5.1
CHECKIN_5.1.2
CHECKIN_5.1.1
```

## scenario_E

:heavy_check_mark:
:warning: Complete `actions.md` with the checkmark for each action.

A request is made by user B on an item of library A, on-shelf without previous requests,
to be picked up at library B. Librarian A finds this item on the floor and does a
checkin as a security measure. The item is validated and goes in transit.

A librarian C checks the item in, but it stays in transit because it goes to library B.
Impatient, user B tries to request the item again (impossible). Another person, user A,
requests it with pickup at library A.

Librarian B sees this document and wants to borrow it for himself. Before doing a
receive, he tries to do a checkout (→ denied). He forgets to do the receive, but by
chance the requesting person, user B, comes and asks for it. Checkout is done.

User A is impatient as well and tries to request the item again (impossible). User C
requests it with pickup at library C. Librarian A tries to check it out for user C
(→ denied). User B returns the item at library B; the item goes in transit to library A
for user A. User A changes the pickup location to library B. User A waited too long and
cancels his request; the item goes in transit to library C for user C. User C cancels his
request as well; the item is in transit to its owning library. User C adds a request
again with pickup at library A, and removes it just after.

By chance, user B finds the item at library B and borrows it. He brings it back at
library A; the item is on shelf.

```text
ADD_REQUEST_1.1
CHECKIN_1.2.2
CHECKIN_4.2
ADD_REQUEST_4.1
ADD_REQUEST_4.2
CHECKOUT_4.2
CHECKOUT_4.1
ADD_REQUEST_3.2.2.1
ADD_REQUEST_3.2.2.2
CHECKOUT_3.2
CHECKIN_3.2.2.1
CHANGE_PICKUP_LOCATION_4
CANCEL_REQUEST_4.1.2
CANCEL_REQUEST_4.1.1
ADD_REQUEST_5.1
CANCEL_REQUEST_5.2
CHECKOUT_5.1
CHECKIN_3.1.1
```
