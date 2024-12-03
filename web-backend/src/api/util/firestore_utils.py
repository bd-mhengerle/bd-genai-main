from datetime import datetime
from typing import List, Optional
from google.cloud import firestore
from src.api.route_dependencies import db
from google.cloud.firestore import FieldFilter
from dateutil import parser
import json

def fix_firestore_dates(data: dict):
    for key, value in data.items():
        if isinstance(value, list):
            data[key] = [fix_firestore_dates(item) if isinstance(item, dict) else item for item in value]
        elif isinstance(value, dict):
            data[key] = fix_firestore_dates(value)
        elif isinstance(value, datetime):
            data[key] = value.rfc3339()
    return data


def apply_filters (query: firestore.Query, filters: List[str], ignore: Optional[List[str]] = [], dateProps: Optional[List[str]] = []):
    """
    filter: should be an array of the form ["name:operator:value"]
    ignore: should be an array of the form ["name"]. It will be match with the name in the filter and then be ignored
    """
    if not filters:
        return query
    for filter in filters:
        field, op, value = filter.split(":", 2)
        if op == "in":
            value = json.loads(value)
        if field not in ignore:
             if hasattr(value, 'lower') and value.lower() in ["true", "false", "1", "0", "yes", "no","True","False","FALSE","TRUE"]:
                value = value.lower() in ["true", "1", "yes","True","TRUE"]
             if field == "createdAt" or field == "updatedAt" or field in dateProps:
                 value =  parser.parse(value)
             query = query.where(filter=FieldFilter(field, op, value))
    return query
    
def apply_orders_by (query: firestore.Query, order_bys: List[str], ignore: Optional[List[str]] = []):
    """
    filter: should be an array of the form ["name:desc","name:asc"]
    ignore: should be an array of the form ["name"]. It will be match with the name in the orderBy and then be ignored
    """
    if not order_bys:
        return query
    for order_by in order_bys:
        field, direction = order_by.split(":")
        if field not in ignore:
            if direction == "desc":
                query = query.order_by(field, direction=firestore.Query.DESCENDING)
            else:
                query = query.order_by(field, direction=firestore.Query.ASCENDING)
    return query
    
def apply_cursor(query: firestore.Query, collection: str,  cursor: str, ): 
    if cursor is None or  cursor == "":
        return query;
    ref = db.collection(collection).document(cursor).get()
    if not ref.exists:
        return query;
    return query.start_after(ref)