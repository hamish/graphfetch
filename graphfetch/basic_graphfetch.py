from .__init__ import transform_model, transform_model_list, transform_futures_list
from google.appengine.ext import ndb
import types

def attach_source_list(attachment, result):
    child_keys = getattr(result, attachment.key_name)
    children = fetch_basic(attachment.target_fd, keys=child_keys)
    if attachment.sort_key is not None:
        children.sort(key=attachment.sort_key)
    setattr(result, attachment.name, children)
def attach_source_key(attachment, result):
    child_key = getattr(result, attachment.key_name)
    if child_key is not None:
        child = fetch_basic(attachment.target_fd, key=child_key)
    else: 
        child = None
    setattr(result, attachment.name, child)
def attach_target_key(attachment, result):
    filter = ndb.GenericProperty(attachment.key_name) == result.key
    children = fetch_basic(attachment.target_fd, filter=filter, additional_filter=attachment.additional_filter)
    setattr(result, attachment.name, children)

def fetch_basic(fd, future=None, key=None, keys=None, filter=None, additional_filter=None, order=None, transform=transform_model, limit=None, offset=0):
    results=[]
    if keys is not None:
        results = ndb.get_multi(keys)
    elif key is not None:
        results=key.get()
    else:
        qry = fd.kind.query()
        if filter is not None:
            qry=qry.filter(filter)
        if additional_filter is not None:
            qry=qry.filter(additional_filter)
        if order is not None:
            qry = qry.order(order)
        results =qry.fetch(limit=limit, offset=offset)
    
    for attachment in fd.source_list_attachments:
        if isinstance(results, types.ListType):
            for result in results:
                attach_source_list(attachment, result)
        else:
            attach_source_list(attachment, results)
    for attachment in fd.source_key_attachments:
        if isinstance(results, types.ListType):
            for result in results:
                attach_source_key(attachment, result)
        else:
            attach_source_key(attachment, results)
    for attachment in fd.target_key_attachments:
        if isinstance(results, types.ListType):
            for result in results:
                attach_target_key(attachment, result)
        else:
            attach_target_key(attachment, results)            
    return results
def fetch_page_basic(fd, page_size, start_cursor=None, filter=None, additional_filter=None, order=None, transform=transform_model,):
    results=[]
    return results