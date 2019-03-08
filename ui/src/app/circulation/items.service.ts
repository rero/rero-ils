import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { mergeMap, map, catchError, concatAll } from 'rxjs/operators';
import { of } from 'rxjs';
import { Item, ItemAction } from './items';

@Injectable({
  providedIn: 'root'
})
export class ItemsService {

  constructor(private http: HttpClient) { }

  getRequestedLoans(libraryPid) {
    const url = `/api/item/requested_loans/${libraryPid}`;
    return this.http.get<any>(url).pipe(
      map(data => data.hits),
      map(hits => hits.total === 0 ? [] : hits.hits),
      map(hits => hits.map(
        data => {
          const item = data.item;
          if (data.loan) {
            item.loan = data.loan;
          }
          return item;
        }
        ))
      );
  }

  doValidateRequest(item) {
    const url = '/api/item/validate';
    return this.http.post<any>(url, {
      item_pid: item.pid,
      loan_pid: item.loan.loan_pid
    }).pipe(
    map(data => {
      const itemData = data.metadata;
      itemData.loan = data.action_applied.validate;
      return itemData;
    })
    );
  }

  getItem(barcode: string) {
    return this.http.get<any>(`/api/item/barcode/${barcode}`).pipe(
      map(data => {
        return data.metadata;
      }),
      map(data => {
        const item = new Item(data.item);
        if (data.loan) {
          item.setLoan(data.loan);
        }
        return item;
      }),
      catchError(e => {
        if (e.status === 404) {
          return of(null);
        }
      })
      );
  }

  automaticCheckin(itemBarcode) {
    const url = '/api/item/automatic_checkin';
    return this.http.post<any>(url, {'item_barcode': itemBarcode}).pipe(
      map(data => {
        const item = new Item(data.metadata);
        const action = Object.keys(data.action_applied).pop();
        const loan = Object.values(data.action_applied).pop();
        if (loan) {
          item.setLoan(loan);
        }
        item.actionDone = ItemAction[action];
        return item;
      }),
      catchError(e => {
        if (e.status === 404) {
          return of(null);
        }
      })
      );
  }

  doAction(item, patron_pid?: string) {
    const action = item.currentAction;
    const url = `/api/item/${action}`;
    const data = {
      item_pid: item.pid
    };
    if (patron_pid && action === ItemAction.checkout) {
      data['patron_pid'] = patron_pid;
    }
    if (item.loan) {
      data['loan_pid'] = item.loan.loan_pid;
    }
    return this.http.post<any>(url, data).pipe(
      map(itemData => {
        const newItem = new Item(itemData.metadata);
        newItem.actionDone = action;
        newItem.setLoan(Object.values(itemData.action_applied).pop());
        return newItem;
      })
      );
  }
}
