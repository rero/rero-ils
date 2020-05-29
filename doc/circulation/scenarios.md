# **Circulation scenarios**

## Name of the scenario

 short description
````
action_1  [action parameters or notes]
action_2  [action parameters or notes]
action_3  [action parameters or notes]
````
## scenario_A (standard loan)

:heavy_check_mark:

A request is made on on-shelf item, that has no requests, to be picked up at the owning library. Validated by the librarian. Picked up at same owning library. and returned on-time at the owning library

````
ADD_REQUEST_1.1 [item, pickup_library, patron]
VALIDATE_1.2    [librarian, transaction_library, loan]
CHECKOUT_2.1    [librarian, transaction_library, loan]
CHECKIN_3.1.1     [librarian, transaction_library, loan]
````

## scenario_B (standard loan with transit)

:heavy_check_mark:

A request is made on item of library A, on-shelf without previous requests, to be picked up at library B. Validated by the librarian A and goes in transit. Received by the librarian B and goes at desk. Picked up at library B. Returned on-time at the library B, goes in transit. Received at library A and goes on shelf.

````
ADD_REQUEST_1.1
VALIDATE_1.2
CHECKIN_4.1
CHECKOUT_2.1
CHECKIN_3.1.2
CHECKIN_5.1.1
````

## scenario_C (item with multiple in_transit requests)

:heavy_check_mark:

A request is made on item of library A, on-shelf without previous requests, to be picked up at library B. Validated by the librarian A and goes in transit. Received by the librarian B and goes at desk. Picked up at library B. Requested by another patron_2 to be picked up at library C. Returned on-time at the library B, goes in transit to library C. Received at library C and goes at desk. Picked up at library C by patron_2. Renewed by patron_2. Returned on-time at the library C after the end of first renewal. goes in transit to library A. Received at library A and goes on shelf.

````
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
````

## scenario_D (denied actions and unconventional workflow)

:heavy_check_mark: 

An inexperienced librarian A (library A) makes a checkin on item A, which is on shelf at library A and without requests (-> nothing happens). Item A is requested by patron A. Another librarian B of library B tries to check it out for patron B (-> denied). The item is requested by patron B with pickup library B. Librarian B tries again to check it out for patron B (-> denied), then for patron A (-> ok). Patron A tries to renew item A (-> denied). Patron A returns item A at library B. The item is at desk for patron B.

Patron A requests it again, with pickup library A. Unexpectedly, libarian A tries to check out item A for patron A (-> denied). He then checks it out for patron B. Patron B returns item A at library C. It goes in transit to library A for patron A.

Before arriving to library A, it transits through library B. Patron A cancels his request. Item A transits through library C. It is then received at its owning library A.

````
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
````

## scenario_E

*WORK IN PROGRESS*

A request is made by user B on item of library A, on-shelf without previous requests, to be picked up at library B. Librarian A finds this item on the floor and does a checkin, by security. The item is validated and goes in transit.

A librarian C checks the item in, but it stays in transit, because it goes to library B. Impatient, user B tries to request again the item (impossible). Another person, user A, requests it with pickup at library A.

A librarian B sees this document and wants to borrow it for himself. Before doing a *receive*, he tries to do a checkout (-> denied). He definitely forgots to do the receive, but by chance the requesting person, user B, come and ask for it. Checkout is done.

User A is impatient as well and tries to request the item again (impossible). User C requests it with pickup library C. Librarian A tries to check it out for user C (-> denied). User B returns the item at library A; a checkin is done from the checkout interface. Item is directly at desk for user A.


```
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
CHECKOUT_3.1
```
