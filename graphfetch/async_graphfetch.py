#!/usr/bin/env python
##
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

__author__  = 'Hamish Currie'
import logging
import types
from google.appengine.ext import ndb
from .__init__ import transform_model, transform_model_list, transform_futures_list

#def transform_model(instance):
#    if not isinstance(instance, ndb.Model):
#        raise Exception("Attempting to transform object which is not an ndb Model: %s" % str(instance))
#    setattr(instance, 'id', instance.key.id())
#    for key in dir(instance):
#        value = getattr(instance, key)
#    return instance
#
#def transform_model_list(entities, transform=transform_model):
#    if isinstance(entities, types.ListType):
#        return [transform(e) for e in entities]
#    else:
#        return transform(entities)
#
#def transform_futures_list(futures):
#    return [transform_model(f.get_result()) for f in futures]

SOURCE_LIST='SOURCE_LIST'
TARGET_KEY='TARGET_KEY'
SOURCE_KEY='SOURCE_KEY'


class FetchDefinition():
    def __init__(self, kind):
        self.kind = kind
        self.source_list_attachments=[]
        self.target_key_attachments=[]
        self.source_key_attachments=[]
        
    class Attachment():
        def __init__(self, target_fd, name, key_name, attachment_type, additional_filter=None, order=None):
            #logging.info("Attachment: %s %s %s %s" %(target_fd, name, key_name, additional_filter))
            self.target_fd = target_fd
            self.name=name
            self.key_name=key_name
            self.additional_filter=additional_filter
            self.attachment_type=attachment_type
            self.order=order
        
    def attach(self, kind, attachment_type, name=None, key_name=None, additional_filter=None, order=None):
        target_fd = FetchDefinition(kind)
        kind_name=kind.__name__.lower()
        if attachment_type == SOURCE_LIST:
            if name is None:
                name="%ss" % kind_name
            if key_name is None:
                key_name = "%s_keys" % kind_name
            self.source_list_attachments.append(FetchDefinition.Attachment(target_fd, name, key_name, attachment_type, additional_filter, order))
        elif attachment_type == TARGET_KEY:
            if name is None:
                name="%ss" % kind_name
            if key_name is None:
                source_kind_name = self.kind.__name__.lower()
                key_name="%s_key" % source_kind_name
            self.target_key_attachments.append(FetchDefinition.Attachment(target_fd, name, key_name, attachment_type, additional_filter, order))
        elif attachment_type== SOURCE_KEY:
            if name is None:
                name="%s" % kind_name
            if key_name is None:
                key_name = "%s_key" % kind_name
            self.source_key_attachments.append(FetchDefinition.Attachment(target_fd, name, key_name, attachment_type, additional_filter, order))
        else:
            raise Exception("Fetch.attach called with invalid type parameter: [%s]" %(attachment_type))
        return target_fd

def get_values_from_future(future):
    values=[]    
    #logging.info ("get_values_from_future: %s " % future)
    if isinstance(future, types.ListType):
        for f in future:
            values.append(f.get_result())
    elif future is not None:
        values=future.get_result()
    return values

def get_qry_from_filter(fd, filter, additional_filter=None, order=None):
    qry = fd.kind.query()
    if filter:
        qry=qry.filter(filter)
    if additional_filter is not None:
        qry=qry.filter(additional_filter)
    if order is not None:
        qry=qry.order(order)
    return qry
def get_futures_from_qry(fd, filter, additional_filter=None, order=None):
    qry=get_qry_from_filter(fd, filter, additional_filter, order)
    logging.info("get_futures_from_qry: %s" % str(qry))
    values=qry.fetch_async()
    return values

def get_futures_from_keys(fd, keys):
    futures=[]
    if isinstance(keys, types.ListType):
        futures = ndb.get_multi_async(keys)
    else:
        futures = keys.get_async()
    return futures

def get_target_key_future(fd, key, target_key_futures):
    for a in fd.target_key_attachments:
        filter = ndb.GenericProperty(a.key_name) == key
        future = get_futures_from_qry(a.target_fd,filter=filter, additional_filter=a.additional_filter, order=a.order)
        target_key_futures.append(future)
def get_target_key_futures(fd, keys):
    target_key_futures=[]
    if not isinstance(keys, types.ListType):
        future = get_target_key_future(fd, keys,target_key_futures)
    else:
        for key in keys:
            future = get_target_key_future(fd, key,target_key_futures)
    return target_key_futures

def get_value_future(fd, future, key, keys, filter, additional_filter):
    value_future = None
    if future is not None:
        logging.info("gvf: future")
        value_future = future
    elif key is not None:
        logging.info("gvf: key")
        value_future=get_futures_from_keys(fd, key)
    elif keys is not None:
        logging.info("gvf: keys")
        value_future=get_futures_from_keys(fd, keys)
    else:
        logging.info("gvf: filter")
        value_future= get_futures_from_qry(fd, filter, additional_filter)
    return value_future

def get_key_dict(values):
    if isinstance(values, types.ListType):
        return dict((v.key,v) for v in values)
    else:
        d={}
        d[values.key]=values
        return d

def get_keys(values):
    if isinstance(values, types.ListType):
        keys =[]
        for v in values:
            keys.append(v.key)
        return keys
    else:
        return [values.key]

def populate_target_key_lists(source, attachments):
    for a in attachments:
        if not hasattr(source, a.name):
            setattr(source, a.name, [])

def populate_target_key_lists_for_values(values, attachments):
    if isinstance(values, types.ListType):
        for source in values:
            populate_target_key_lists(source, attachments)
    else:
        populate_target_key_lists(values, attachments)

def recurse_attachment_with_future(attachment, futures, value, transform=transform_model):
    future = futures.pop(0)
    if attachment.attachment_type==SOURCE_KEY:
        if len(future)>0:
            future=future[0]
        else:
            setattr(value,attachment.name, None)
            return
    target_values=fetch_async(attachment.target_fd, future=future,transform=transform)
    logging.info("setting %s" % attachment.name)
    setattr(value, attachment.name, target_values)

def add_attachment_future(attachment, futures, value):    
    keys = getattr(value, attachment.key_name)
    if attachment.attachment_type == SOURCE_KEY:
        if keys is not None:
            keys=[keys]
        else:
            keys=[]
    future = get_futures_from_keys(attachment.target_fd, keys)
    futures.append(future)
def apply(attachments, futures, values, func, kwargs):
    for a in attachments:
        if isinstance(values, types.ListType):
            for source in values:
                func(a,futures,source, **kwargs)
        else:
            func(a,futures,values, **kwargs)
            
def recurse_attachments_with_future(attachments, futures, values, transform=transform_model):
    return apply(attachments, futures, values, recurse_attachment_with_future, {'transform':transform})
def add_attachment_futures(attachments, futures, values):
    return apply(attachments, futures, values, add_attachment_future,{})

def attach_target_key_values(fd, target_key_futures, values, transform):
    # append target_key objects to the lists that were pre-created earlier
    if not isinstance(values, types.ListType):
        for a in fd.target_key_attachments:
            future = target_key_futures.pop(0)
            target_values = fetch_async(a.target_fd,future=future, transform=transform)
            setattr(values, a.name, target_values)
    else:
        for value in values:
            for a in fd.target_key_attachments:
                future = target_key_futures.pop(0)
                target_values = fetch_async(a.target_fd,future=future, transform=transform)
                setattr(value, a.name, target_values)
                
def fetch_async(fd, future=None, key=None, keys=None, filter=None, additional_filter=None, order=None, transform=transform_model):
    # If the datastore retrieve for this iteration is not already running, get it started now.
    value_future = get_value_future(fd, future, key, keys, filter, additional_filter)

    target_key_futures=[]
    source_list_futures=[]
    source_key_futures=[]
    # If we know the keys in advance, we can start any target_key child queries before waiting 
    # for the current objects to be available.
    # Note that we are doing the query for the set of objects in one go, we will assign them
    # to appropriate objects after retrieval.
    if keys is not None:
        logging.info("Early target_key")
        target_key_futures = get_target_key_futures(fd,keys)

    # wait for the current objects to be available, then do any transformations to them.
    values=get_values_from_future(value_future)
    values = transform_model_list(values, transform=transform)
    
    k = get_keys(values)
    
    # Start any queries that could not be started earlier 
    if keys is None:
        logging.info("Late target_key: %s" % k)
        target_key_futures = get_target_key_futures(fd,k)

    add_attachment_futures(fd.source_key_attachments, source_key_futures, values)
    add_attachment_futures(fd.source_list_attachments, source_list_futures, values)
    
    # create the list attributes for target_key attachments.
    #populate_target_key_lists_for_values(values, fd.target_key_attachments)
    
    recurse_attachments_with_future(fd.source_key_attachments, source_key_futures, values, transform=transform)
    recurse_attachments_with_future(fd.source_list_attachments, source_list_futures, values, transform=transform)
    attach_target_key_values(fd, target_key_futures, values, transform)
        
    return values

def fetch_page_async(fd, page_size, start_cursor=None, filter=None, additional_filter=None, order=None, transform=transform_model,):
    
    qry=get_qry_from_filter(fd, filter, additional_filter, order)
    values, next_curs, more = qry.fetch_page(page_size, start_cursor=start_cursor)
    k = get_keys(values)
    source_list_futures=[]
    source_key_futures=[]
    target_key_futures = get_target_key_futures(fd, k)
    add_attachment_futures(fd.source_key_attachments, source_key_futures, values)
    add_attachment_futures(fd.source_list_attachments, source_list_futures, values)
    # create the list attributes for target_key attachments.
    populate_target_key_lists_for_values(values, fd.target_key_attachments)
    
    recurse_attachments_with_future(fd.source_key_attachments, source_key_futures, values, transform=transform)
    recurse_attachments_with_future(fd.source_list_attachments, source_list_futures, values, transform=transform)
    attach_target_key_values(fd, target_key_futures, values, transform)

    
    return values, next_curs, more