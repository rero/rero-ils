# **Circulation Actions**

## Add a request

### required_parameters:

    item_pid_value
    pickup_location_pid
    patron_pid
    transaction_location_pid or transaction_library_pid
    transaction_user_pid

1. :100: __ADD_REQUEST_1__: item on_shelf (no current loan)
    1. :white_check_mark: :white_check_mark: :white_check_mark: :white_check_mark: __ADD_REQUEST_1_1__: PENDING loan does not exist →  (add loan PENDING)
    1. __ADD_REQUEST_1_2__: PENDING loan exists
        1. __ADD_REQUEST_1_2_1__: request patron = current loan patron → request denied
        1. :white_check_mark: __ADD_REQUEST_1_2_2__: request patron != current loan patron →  (add loan PENDING)
1. :100: __ADD_REQUEST_2__: item at_desk, requested (ITEM_AT_DESK) 
    1. __ADD_REQUEST_2_1__: request patron = current loan patron → request denied
    1. :white_check_mark: __ADD_REQUEST_2_2__: request patron != current loan patron →  (add loan PENDING)
1. :100: __ADD_REQUEST_3__: item on_loan (ITEM_ON_LOAN) 
    1. __ADD_REQUEST_3_1__: request patron = current loan patron → request denied
    1. __ADD_REQUEST_3_2__: request patron != current loan patron:
        1. :white_check_mark: __ADD_REQUEST_3_2_1__: PENDING loan does not exist →  (add loan PENDING)
        1. __ADD_REQUEST_3_2_2__: PENDING loan exists
            1. __ADD_REQUEST_3_2_2_1__: request patron = PENDING loan patron → request denied
            1. __ADD_REQUEST_3_2_2_2__: request patron != PENDING loan patron →  (add loan PENDING)
1. :100: __ADD_REQUEST_4__: item in_transit (IN_TRANSIT_FOR_PICKUP)
    1. __ADD_REQUEST_4_1__: request patron = current loan patron → request denied
    1. __ADD_REQUEST_4_2__: request patron != current loan patron →  (add loan PENDING)
1. :100: __ADD_REQUEST_5__: item in_transit (IN_TRANSIT_TO_HOUSE)
    1. __ADD_REQUEST_5_1__: PENDING loan does not exist →  (add loan PENDING)
    1. __ADD_REQUEST_5_2__: PENDING loan exists
        1. __ADD_REQUEST_5_2_1__: request patron = current loan patron → request denied
        1. __ADD_REQUEST_5_2_2__: request patron != current loan patron →  (add loan PENDING)


## Cancel request

### required_parameters:

    pid (loan pid)
    transaction_location_pid or transaction_library_pid
    transaction_user_pid

1. :100: __CANCEL_REQUEST_1__: item on_shelf (no current loan)
	1. __CANCEL_REQUEST_1_1__: PENDING loan does not exist → (cancel not possible)
	1. __CANCEL_REQUEST_1_2__: PENDING loan exists → (cancel loan, item is: on_shelf)

1. :100: __CANCEL_REQUEST_2__: item at_desk, requested (ITEM_AT_DESK)
	1. __CANCEL_REQUEST_2_1__: loan to cancel = current loan
		1. __CANCEL_REQUEST_2_1_1__: PENDING loan does not exist Make it impossible to cancel loan from public interface. Future: make it possible and give an alert to the library that the item should not stayed at desk
			1. __CANCEL_REQUEST_2_1_1_1__: item library != pickup location of current loan → (update loan to IN_TRANSIT_TO_HOUSE, item is: in_transit)
			1. __CANCEL_REQUEST_2_1_1_2__: item library = pickup location of current loan → (cancel loan, item is: on_shelf)
		1. __CANCEL_REQUEST_2_1_2__: PENDING loan exists
			1. __CANCEL_REQUEST_2_1_2_1__: pickup location of 1st pending loan != pickup location of current loan → (cancel loan, item is: in_transit (IN_TRANSIT_FOR_PICKUP))[automatic validate next PENDING loan]
			1. __CANCEL_REQUEST_2_1_2_2__: pickup location of 1st pending loan = pickup location of current loan → (cancel loan, item is: at_desk (ITEM_AT_DESK))[automatic validate next PENDING loan]
	1. __CANCEL_REQUEST_2_2__: loan to cancel != current loan → (cancel loan, item is: at desk)

1. :100: __CANCEL_REQUEST_3__: item on_loan (ITEM_ON_LOAN)
	1. __CANCEL_REQUEST_3_1__: loan to cancel = current loan → (cancel not possible)
	1. __CANCEL_REQUEST_3_2__: loan to cancel != current loan → (cancel loan, item is: on_loan (ITEM_ON_LOAN))

1. :100: __CANCEL_REQUEST_4__: item in_transit (IN_TRANSIT_FOR_PICKUP)
	1. __CANCEL_REQUEST_4_1__: loan to cancel = current loan
		1. __CANCEL_REQUEST_4_1_1__: PENDING loan does not exist → (update loan, item is: in_transit (IN_TRANSIT_TO_HOUSE))
		1. __CANCEL_REQUEST_4_1_2__: PENDING loan exists → (cancel loan, item is: in_transit (IN_TRANSIT_FOR_PICKUP))[automatic validate logic is applied next PENDING loan] 
		
	1. __CANCEL_REQUEST_4_2__: loan to cancel != current loan → (cancel loan, item is: in_transit (IN_TRANSIT_FOR_PICKUP))

1. :100: __CANCEL_REQUEST_5__: item in_transit (IN_TRANSIT_TO_HOUSE)
	1. __CANCEL_REQUEST_5_1__: loan to cancel = current loan
		1. __CANCEL_REQUEST_5_1_1__: PENDING loan does not exist → (checkin the IN_TRANSIT_TO_HOUSE loan, item will  go on shelf  and the loan is cancelled).
		1. __CANCEL_REQUEST_5_1_2__: PENDING loan exists → (cancel loan, item is: in_transit (IN_TRANSIT_FOR_PICKUP))[automatic validate next PENDING loan]
	1. __CANCEL_REQUEST_5_2__: loan to cancel != current loan → (cancel loan, item is: in_transit (IN_TRANSIT_TO_HOUSE)) This use case should in principle never happen.


## Checkout form

### required_parameters:

    item_pid_value
    patron_pid
    transaction_location_pid or transaction_library_pid
    transaction_user_pid

1. :100: __CHECKOUT_1__: item on_shelf (no current loan)
    1. __CHECKOUT_1_1__: PENDING loan does not exist →  (add loan ITEM_ON_LOAN)
    1. PENDING loan exists
        1. :white_check_mark: __CHECKOUT_1_2_1__: checkout patron = patron of first PENDING loan →  (add loan ITEM_ON_LOAN)
        1. :white_check_mark: :white_check_mark: __CHECKOUT_1_2_2__: checkout patron != patron of first PENDING loan →  checkout denied
1. :100: __CHECKOUT_2__: item at_desk, requested (ITEM_AT_DESK)
    1. :white_check_mark: :white_check_mark: :white_check_mark: :white_check_mark: __CHECKOUT_2_1__: checkout patron = patron of first PENDING loan →  (add loan ITEM_ON_LOAN)
    1. :white_check_mark: __CHECKOUT_2_2__: checkout patron != patron of first PENDING loan →  checkout denied
1. :100: __CHECKOUT_3__: item on_loan
    1. __CHECKOUT_3_1__: checkout patron = patron of current loan →  do a checkin
    2. __CHECKOUT_3_2__: checkout patron != patron of current loan →  checkout denied
1. :100: __CHECKOUT_4__: item in_transit (IN_TRANSIT_FOR_PICKUP)
    1. __CHECKOUT_4_1__: checkout patron = patron of current loan →  (add loan ITEM_ON_LOAN) [automatic receive]
    1. __CHECKOUT_4_2__: checkout patron != patron of current loan →  checkout denied
1. :100: __CHECKOUT_5__: item in_transit (IN_TRANSIT_TO_HOUSE)
    1. __CHECKOUT_5_1__: PENDING loan does not exist →  (add loan ITEM_ON_LOAN) [cancel previous loan]
    1. PENDING loan exists
        1. __CHECKOUT_5_2_1__: checkout patron = patron of first PENDING loan →  (add loan ITEM_ON_LOAN) [cancel previous loan]
        1. __CHECKOUT_5_2_2__: checkout patron != patron of first PENDING loan → checkout denied

## Checkin form

### required_parameters for frontend calls:

    item_pid or item_barcode
    transaction_location_pid or transaction_library_pid
    transaction_user_pid

### required_parameters for backend calls:

    pid (loan pid)
    transaction_location_pid or transaction_library_pid
    transaction_user_pid


1. :100:__CHECKIN_1__: item on_shelf (no current loan)
	1. __CHECKIN_1_1__: PENDING loan does not exist
		1. :white_check_mark: __CHECKIN_1_1_1__: item library = transaction library →  (no action, item is: on_shelf)
		1. __CHECKIN_1_1_2__: item library != transaction library →  *item is: in_transit (item status is updated and no loan is created)*
	1. __CHECKIN_1_2__: PENDING loan exists
		1. __CHECKIN_1_2_1__: pickup library of first PENDING loan = transaction library →  (validate first PENDING loan, item is: at_desk (ITEM_AT_DESK))
		1. __CHECKIN_1_2_2__: pickup location of first pending loan != transaction library →  (validate first PENDING loan, item is: in_transit (IN_TRANSIT_FOR_PICKUP))
1. :100:__CHECKIN_2__: item at_desk, requested (ITEM_AT_DESK)
	1. __CHECKIN_2_1__: pickup location = transaction library →  (no action, item is: at_desk (ITEM_AT_DESK))
	1. __CHECKIN_2_2__: pickup location != transaction library →  *item is: in_transit (IN_TRANSIT_FOR_PICKUP)*
1. :100: __CHECKIN_3__: item on_loan
	1. __CHECKIN_3_1__: PENDING loan does not exist
		1. :white_check_mark: __CHECKIN_3_1_1__: item location = transaction library →  (checkin current loan, item is: on_shelf)
		1. :white_check_mark: :white_check_mark: __CHECKIN_3_1_2__: item location != transaction library →  (checkin current loan, item is: in_transit (IN_TRANSIT_TO_HOUSE))
	1. __CHECKIN_3_2__: PENDING loan exists
		1. :white_check_mark: __CHECKIN_3_2_1__: pickup location of first PENDING loan = transaction library →  (checkin current loan, item is: at_desk)[the current loan is returned, automatic validate first PENDING loan]
		1. __CHECKIN_3_2_2__: pickup location of first PENDING loan != transaction library
			1. :white_check_mark: __CHECKIN_3_2_2_1__: pickup location of first PENDING loan = item library →  (checkin current loan, item is: in_transit, cancel current loan and first pending loan to (IN_TRANSIT_FOR_PICKUP))
			1. :white_check_mark: __CHECKIN_3_2_2_2__: pickup location of first PENDING loan != item library →  (checkin current loan, item is: in_transit, cancel current loan and pending loan to (IN_TRANSIT_FOR_PICKUP))
1. :100:__CHECKIN_4__: item in_transit (IN_TRANSIT_FOR_PICKUP)
	1. :white_check_mark: :white_check_mark: :white_check_mark: __CHECKIN_4_1__: pickup location = transaction library →  (delivery_receive current loan, item is: at_desk(ITEM_AT_DESK))
	1. __CHECKIN_4_2__: pickup location != transaction library →  (no action, item is: in_transit (IN_TRANSIT_FOR_PICKUP)) *Future: would be useful to track that an intermediary checkin has been made*
1. :100:__CHECKIN_5__: item in_transit (IN_TRANSIT_TO_HOUSE)
	1. __CHECKIN_5_1__: PENDING loan does not exist
		1. :white_check_mark: :white_check_mark: :white_check_mark: __CHECKIN_5_1_1__: item location = transaction library →  (house_receive current loan, item is: on_shelf)
		1. :white_check_mark: __CHECKIN_5_1_2__: item location != transaction library →  (no action, item is: in_transit (IN_TRANSIT_TO_HOUSE)) *Future: would be useful to track that an intermediary checkin has been made*
	1. __CHECKIN_5_2__: PENDING loan exists
		1. __CHECKIN_5_2_1__: pickup location of first PENDING loan = transaction library
			1. __CHECKIN_5_2_1_1__: pickup location of first PENDING loan = item library →  (house_receive current loan, item is: at_desk(ITEM_AT_DESK))[automatic validate first PENDING loan]
			1. __CHECKIN_5_2_1_2__: pickup location of first PENDING loan != item library →  (cancel current loan, item is: at_desk(ITEM_AT_DESK))[automatic validate first PENDING loan] *It is the case if the first PENDING loan has been deleted or unpriorised since last checkin*
		1. __CHECKIN_5_2_2__: pickup location of first PENDING loan != transaction library
			1. :white_check_mark: __CHECKIN_5_2_2_1__: pickup location of first PENDING loan = item library →  (no action, item is: in_transit (IN_TRANSIT_TO_HOUSE)) *Future: would be useful to track that an intermediary checkin has been made*
			1. __CHECKIN_5_2_2_2__: pickup location of first PENDING loan != item library →  (checkin current loan, item is: in_transit (IN_TRANSIT_FOR_PICKUP))[automatic cancel current loan, automatic validate first PENDING loan] *It is the case if the first PENDING loan has been deleted or unpriorised since last checkin*

## Manual validate

#### required_parameters:
    pid (loan pid)
    transaction_location_pid or transaction_library_pid,
    transaction_user_pid

1. :100:__VALIDATE_1__: item on_shelf (no current loan)
	1. __VALIDATE_1_1__: PENDING loan does not exist →  (validate not possible)
	1. :white_check_mark: :white_check_mark: :white_check_mark: __VALIDATE_1_2__: PENDING loan exists
		1. __VALIDATE_1_2_1__: pickup library of first PENDING loan = transaction library → (validate first PENDING loan, loan is: ITEM_AT_DESK)
		1. __VALIDATE_1_2_2__: pickup library of first PENDING loan != transaction library → (validate first PENDING loan, loan is: IN_TRANSIT_FOR_PICKUP)

1. :100:__VALIDATE_2__: item at_desk, requested (ITEM_AT_DESK) → (manual validate current loan not possible)
1. :100:__VALIDATE_3__: item on_loan (ITEM_ON_LOAN) →  (manual validate current loan not possible)
1. :100:__VALIDATE_4__: item in_transit (IN_TRANSIT_FOR_PICKUP) →  (manual validate current loan not possible)
1. :100:__VALIDATE_5__: item in_transit (IN_TRANSIT_TO_HOUSE) →  (manual validate current loan not possible)


## Extend

### required_parameters:

    item_pid_value
    transaction_location_pid
    transaction_user_pid

1. :100: __EXTEND_1__: item on_shelf (no current loan) →  (extend not possible)
1. :100: __EXTEND_2__: item at_desk, requested (ITEM_AT_DESK) →  (extend not possible)
1. :100: __EXTEND_3__: item on_loan (ITEM_ON_LOAN)
	1. :white_check_mark: __EXTEND_3_1__: PENDING loan does not exist →  (extend current loan)
	1. :white_check_mark: __EXTEND_3_2__: PENDING loan exists →  (extend denied)
1. :100: __EXTEND_4__: item in_transit (IN_TRANSIT_FOR_PICKUP) →  (extend not possible)
1. :100: __EXTEND_5__: item in_transit (IN_TRANSIT_TO_HOUSE) →  (extend not possible)



## update_loan


### Change request pickup location

##### required_parameters:
    pid (loan pid)
	pickup_location_pid

1. :100: __CHANGE_PICKUP_LOCATION_1__: item on_shelf (no current loan)
	1. __CHANGE_PICKUP_LOCATION_1_1__: PENDING loan does not exist →  (change not possible)
	1. __CHANGE_PICKUP_LOCATION_1_2__: PENDING loan exists →  (change possible)
1. :100: __CHANGE_PICKUP_LOCATION_2__: item at_desk, requested (ITEM_AT_DESK)
    1. __CHANGE_PICKUP_LOCATION_2_1__: loan to change = current loan →  (change denied) *Future: make it possible and give an alert to the library that the item should not stayed at desk*
	1. __CHANGE_PICKUP_LOCATION_2_2__: loan to change != current loan →  (change possible)
1. :100: __CHANGE_PICKUP_LOCATION_3__: item on_loan (ITEM_ON_LOAN)
	1. __CHANGE_PICKUP_LOCATION_3_1__: loan to change = current loan →  (change not possible)
	1. __CHANGE_PICKUP_LOCATION_3_2__: loan to change != current loan →  (change possible)
1. :100: __CHANGE_PICKUP_LOCATION_4__: item in_transit (IN_TRANSIT_FOR_PICKUP) → (change possible)
1. :100: __CHANGE_PICKUP_LOCATION_5__: item in_transit (IN_TRANSIT_TO_HOUSE) → (change not possible)


## Move request to first priority

1. __REQUEST_TO_FIRST_RANK_1__: item on_shelf (no current loan)
	1. __REQUEST_TO_FIRST_RANK_1_1__: 1 or 0 PENDING loan exists →  (move not possible)
	1. __REQUEST_TO_FIRST_RANK_1_2__: More than 1 PENDING loans exist →  (move loan to 1st PENDING)
1. __REQUEST_TO_FIRST_RANK_2__: item at_desk, requested (ITEM_AT_DESK)
	1. __REQUEST_TO_FIRST_RANK_2_1__: 1 or 0 PENDING loan exists (additionally to current loan) →  (move not possible)
	1. __REQUEST_TO_FIRST_RANK_2_2__: More than 1 PENDING loans exist →  (move loan to 1st PENDING)
1. __REQUEST_TO_FIRST_RANK_3__: item on_loan (ITEM_ON_LOAN)
	1. __REQUEST_TO_FIRST_RANK_3_1__: 1 or 0 PENDING loan exists (additionally to current loan) →  (move not possible)
	1. __REQUEST_TO_FIRST_RANK_3_2__: More than 1 PENDING loans exist →  (move loan to 1st PENDING)
1. __REQUEST_TO_FIRST_RANK_4__: item in_transit (IN_TRANSIT_FOR_PICKUP)
	1. __REQUEST_TO_FIRST_RANK_4_1__: 1 or 0 PENDING loan exists (additionally to current loan) →  (move not possible)
	1. __REQUEST_TO_FIRST_RANK_4_2__: More than 1 PENDING loans exist →  (move loan to 1st PENDING) *Future option: make possible to move before current loan*
1. __REQUEST_TO_FIRST_RANK_5__: item in_transit (IN_TRANSIT_TO_HOUSE)
	1. __REQUEST_TO_FIRST_RANK_5_1__: 1 or 0 PENDING loan exists (additionally to current loan) →  (move not possible)
	1. More than 1 PENDING loans exist
		1. __REQUEST_TO_FIRST_RANK_5_2_1__: pickup location of PENDING loan to move = item library →  (move loan to 1st PENDING, item is: in_transit (IN_TRANSIT_TO_HOUSE))
		1. __REQUEST_TO_FIRST_RANK_5_2_2__: pickup location of PENDING loan to move != item library →  (move loan to 1st PENDING, item is: in_transit (IN_TRANSIT_FOR_PICKUP))[automatic cancel current loan]

# TODO

* evaluate if we need to extend invenio-circulation or do it in RERO ILS
* is item status always determined by loans in state charts or can we set it abitrary
* NPR: important simplifications are possible if an item with pending loan is always IN_TRANSIT_FOR_PICKUP, instead of being sometimes IN_TRANSIT_TO_HOUSE:
    * __CHECKIN_5__: point 2 of "Checkin"
    * __CANCEL_REQUEST_5__: point 2.2 of "Cancel request"
    * __REQUEST_TO_FIRST_RANK_5__: point 2.2 of "Move request to first priority"
    * __ADD_REQUEST_5__: point 1 of "Add a request"
    * __CHANGE_PICKUP_LOCATION_5__: point 5 of "Change request pickup location"

# NOTES

* :100: means that the action is already implemented in the backend
* :white_check_mark: means the action appeared in one scenario.

## Suggestions

In order to be less verbose, it would be great to use icon instead of long sentence as "pending loan exists and pickup library should be different from transaction library". It could be: :books: + :truck::house::no_entry_sign::dollar::house:

To simplify conditions about each case, we suggest some icons:

* :books: a loan exist (i.e PENDING loan exists).
* :no_entry_sign: means "**NOT**". I.e :no_entry_sign: :books: means loan does not exist (NOT loan). Used with another icon, it means "**different**". I.e :truck::house::no_entry_sign::dollar::house: means "pickup library is different from transaction library"
* :no_entry_sign: :books: loan does not exist
* :busts_in_silhouette: same patron as current loan patron
* :no_entry_sign: :busts_in_silhouette: means patron is different from current loan patron
* icons used to create complex word:
    * :house: library
    * :truck: pickup
    * :notebook: item
    * :triangular_flag_on_post: location
* as:
    * :truck::house: pickup library
    * :truck::triangular_flag_on_post: pickup location
    * :dollar::house: transaction library

