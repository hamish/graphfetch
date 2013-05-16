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

def transform_model_list(entities, transform=transform_model):
    if isinstance(entities, types.ListType):
        return [transform(e) for e in entities if e is not None]
    else:
        return transform(entities)

def transform_futures_list(futures):
    return [transform_model(f.get_result()) for f in futures]

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
        def __init__(self, target_fd, name, key_name, attachment_type, additional_filter=None, order=None, sort_key=None):
            #logging.info("Attachment: %s %s %s %s" %(target_fd, name, key_name, additional_filter))
            self.target_fd = target_fd
            self.name=name
            self.key_name=key_name
            self.additional_filter=additional_filter
            self.attachment_type=attachment_type
            self.order=order
            self.sort_key=sort_key
        
    def attach(self, kind, attachment_type, name=None, key_name=None, additional_filter=None, order=None, sort_key=None):
        target_fd = FetchDefinition(kind)
        kind_name=kind.__name__.lower()
        if attachment_type == SOURCE_LIST:
            if name is None:
                name="%ss" % kind_name
            if key_name is None:
                key_name = "%s_keys" % kind_name
            self.source_list_attachments.append(FetchDefinition.Attachment(target_fd, name, key_name, attachment_type, additional_filter, order, sort_key))
        elif attachment_type == TARGET_KEY:
            if name is None:
                name="%ss" % kind_name
            if key_name is None:
                source_kind_name = self.kind.__name__.lower()
                key_name="%s_key" % source_kind_name
            self.target_key_attachments.append(FetchDefinition.Attachment(target_fd, name, key_name, attachment_type, additional_filter, order, sort_key))
        elif attachment_type== SOURCE_KEY:
            if name is None:
                name="%s" % kind_name
            if key_name is None:
                key_name = "%s_key" % kind_name
            self.source_key_attachments.append(FetchDefinition.Attachment(target_fd, name, key_name, attachment_type, additional_filter, order, sort_key))
        else:
            raise Exception("Fetch.attach called with invalid type parameter: [%s]" %(attachment_type))
        return target_fd

def fetch(fd, future=None, key=None, keys=None, filter=None, additional_filter=None, order=None, transform=transform_model, impl=None, limit=None, offset=0):
    if not impl:
        from .async_graphfetch import fetch_async
        impl = fetch_async
        
    return impl(fd, future=future, key=key, keys=keys, filter=filter, additional_filter=additional_filter, order=order, transform=transform, limit=limit, offset=offset)

def fetch_page(fd, page_size, start_cursor=None, filter=None, additional_filter=None, order=None, transform=transform_model, impl=None):
    if not impl:
        from .async_graphfetch import fetch_page_async
        impl = fetch_page_async
    return  impl(fd, page_size, start_cursor=start_cursor, filter=filter, additional_filter=additional_filter, order=order, transform=transform)
    
