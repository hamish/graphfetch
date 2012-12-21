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


def transform_model(instance):
    if not isinstance(instance, ndb.Model):
        raise Exception("Attempting to transform object which is not an ndb Model: %s" % str(instance))
    setattr(instance, 'id', instance.key.id())
    for key in dir(instance):
        value = getattr(instance, key)
    return instance

def transform_model_list(entities):
    return [transform_model(e) for e in entities]

def transform_futures_list(futures):
    return [transform_model(f.get_result()) for f in futures]

SOURCE_LIST='SOURCE_LIST'
TARGET_KEY='TARGET_KEY'
SOURCE_KEY='SOURCE_KEY'

class Attachment():
    def __init__(self, target_fetch, name, key_name, additional_filter=None):
        logging.info("Attachment: %s %s %s %s" %(target_fetch, name, key_name, additional_filter))
        self.target_fetch = target_fetch
        self.name=name
        self.key_name=key_name
        self.additional_filter=additional_filter

class Fetch():
    def __init__(self, kind):
        self.kind = kind
        self.source_list_attachments=[]
        self.target_key_attachments=[]
        self.source_key_attachments=[]
        
    def attach(self, kind, attachment_type, name=None, key_name=None, additional_filter=None):
        target_fetch = Fetch(kind)
        kind_name=kind.__name__.lower()
        if attachment_type == SOURCE_LIST:
            if name is None:
                name="%ss" % kind_name
            if key_name is None:
                key_name = "%s_keys" % kind_name
            self.source_list_attachments.append(Attachment(target_fetch, name, key_name))
        elif attachment_type == TARGET_KEY:
            if name is None:
                name="%ss" % kind_name
            if key_name is None:
                source_kind_name = self.kind.__name__.lower()
                key_name="%s_key" % source_kind_name
            self.target_key_attachments.append(Attachment(target_fetch, name, key_name))
        elif attachment_type== SOURCE_KEY:
            if name is None:
                name="%s" % kind_name
            if key_name is None:
                key_name = "%s_key" % kind_name
            self.source_key_attachments.append(Attachment(target_fetch, name, key_name))
        else:
            raise Exception("Fetch.attach called with invalid type parameter: [%s]" %(attachment_type))
        return target_fetch

def get_values_from_future(future):
    values=[]    
    logging.info ("get_values_from_future: %s " % future)
    import types
    if isinstance(future, types.ListType):
        for f in future:
            values.append(f.get_result())
    elif filter is not None:
        values=future.get_result()
    return values

def get_futures_from_qry(fetch, key_filter, additional_filter=None):
    qry = fetch.kind.query(key_filter)
    if additional_filter is not None:
        qry=qry.filter(additional_filter)
    values=qry.fetch_async()
    return values

def get_futures_from_keys(fetch, keys):
    values = ndb.get_multi_async(keys)
    return values

def get_target_key_futures(fetch, keys):
    target_key_futures=[]
    for a in fetch.target_key_attachments:
        key_filter = ndb.GenericProperty(a.key_name).IN(keys)
        future = get_futures_from_qry(a.target_fetch,key_filter=key_filter, additional_filter=a.additional_filter)
        target_key_futures.append(future)
    return target_key_futures

def get_value_future(fetch, future, keys, key_filter, additional_filter):
    value_future = None
    if future is not None:
        value_future = future
    elif keys is not None:
        value_future=get_futures_from_keys(fetch, keys)
    elif filter is not None:
        value_future= get_futures_from_qry(fetch, key_filter, additional_filter)
    else:
        raise Exception("get_graph: you must pass one of future, keys or key_filter")
    return value_future

import types
def get_graph(fetch, future=None, keys=None, key_filter=None, additional_filter=None):
    log_future = "None"
    if future is not None:
        log_future="F"
    if isinstance(future, types.ListType):
        log_future="List"
    logging.info("get_graph: fetch:%s, future:%s, keys:%s, key_filter:%s, additional_filter:%s" %(fetch, log_future, keys, key_filter, additional_filter))
    
    value_future = get_value_future(fetch, future, keys, key_filter, additional_filter)

    target_key_futures=[]
    source_list_futures=[]
    source_key_futures=[]
    # If we know the keys in advance, we can start any target_key child queries before waiting 
    # for the current objects to be available.
    # Note that we are doing the query for the set of objects in one go, we will assign them
    # to appropriate objects after retrieval.
    if keys is not None:
        target_key_futures = get_target_key_futures(fetch, keys)

    # wait for the current objects to be available, then do any transformations to them.
    values=get_values_from_future(value_future) 
    values = transform_model_list(values)
    
    
    k=(v.key for v in values)
    values_dict = dict((v.key,v) for v in values)
    # Start any queries that could not be started earlier 
    if keys is None:
        target_key_futures = get_target_key_futures(fetch, k)
        
    for source in values:
        for a in fetch.source_key_attachments:
            key = getattr(source, a.key_name)
            skf = get_futures_from_keys(a.target_fetch, [key])
            source_key_futures.append(skf)
        for a in fetch.target_key_attachments:
            if not hasattr(source, a.name):
                setattr(source, a.name, [])
        for a in fetch.source_list_attachments:
            keys = getattr(source, a.key_name)
            target_values = get_graph(a.target_fetch, keys=keys)
            setattr(source, a.name, target_values)
        for a in fetch.source_key_attachments:
            key = getattr(source, a.key_name)
            target_value = get_graph(a.target_fetch, keys=(key,))[0]
            setattr(source, a.name, target_value)
            
        
    for a in fetch.target_key_attachments:
        future = target_key_futures.pop(0)
        target_values = get_graph(a.target_fetch,future=future)
        for value in target_values:
            source_key = getattr(value, a.key_name)
            source = values_dict[source_key]
            target_attr = getattr(source, a.name)
            target_attr.append(value)        
    for a in fetch.source_key_attachments:
        future=source_key_futures.pop(0)
        
        
    return values

#def get_demo_article(article_id):
#    keys=[ndb.Key(Article, long(article_id)), ]
#    articleFetch = Fetch(kind=Article)
#    articleFetch.attach(kind=Student, attachment_type=SOURCE_LIST)
#    articleFetch.attach(kind=CurriculumItem, attachment_type=SOURCE_LIST, name='learningoutcome', key_name='learningoutcome_keys')
#    articleFetch.attach(kind=Comment, attachment_type=TARGET_KEY, key_name='article', additional_filter=Comment.hidden==False)
#    articleFetch.attach(kind=ArticlePicture, attachment_type=TARGET_KEY, key_name='article')
#    articleFetch.attach(kind=Kindergarten, attachment_type=SOURCE_KEY)
#    articleFetch.attach(kind=Group, attachment_type=SOURCE_KEY)
#    return get_graph(articleFetch, keys=keys)[0]
    