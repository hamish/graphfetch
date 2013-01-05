from .__init__ import transform_model, transform_model_list, transform_futures_list
from google.appengine.ext import ndb

def fetch_basic(fd, future=None, key=None, keys=None, filter=None, additional_filter=None, order=None, transform=transform_model):
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
        results =qry.fetch()
    
    # Attach SOURCE_LIST children
    for attachment in fd.source_list_attachments:
        for result in results:
            child_keys = getattr(result, attachment.key_name)
            children = fetch_basic(attachment.target_fd, keys=child_keys)
            setattr(result, attachment.name, children)
    for attachment in fd.source_key_attachments:
        for result in results:
            child_key = getattr(result, attachment.key_name)
            child = fetch_basic(attachment.target_fd, key=child_key)
            setattr(result, attachment.name, child)
    for attachment in fd.target_key_attachments:
        for result in results:
            filter = ndb.GenericProperty(attachment.key_name) == result.key
            children = fetch_basic(attachment.target_fd, filter=filter, additional_filter = attachment.additional_filter)
            setattr(result, attachment.name, children)
            
    return results
def fetch_page_basic(fd, page_size, start_cursor=None, filter=None, additional_filter=None, order=None, transform=transform_model,):
    results=[]
    return results