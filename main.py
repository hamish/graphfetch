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

__author__ = 'Hamish Currie'

import os
import webapp2
from webapp2_extras.routes import RedirectRoute
from google.appengine.ext import ndb
from google.appengine.api import memcache
import jinja2
import os


import graphfetch
import random
import logging
import testmodels
from orders import Customer, Product, OrderDetail, Order
import orders
    
# utility Methods
def get_order(order_key):
    fetch = graphfetch.FetchDefinition(kind=Order)
    fetch.attach(kind=OrderDetail, attachment_type=graphfetch.SOURCE_LIST)

def get_customer_with_orders_and_details(customer_key):
    customer_fetch=orders.get_full_order_fetchdef()
    customer = graphfetch.fetch(customer_fetch, key=customer_key)
    return customer

#Handlers
class QueryRequestHandler(webapp2.RequestHandler):
    def get(self, customer_id):
        customer_key = ndb.Key(Customer, long(customer_id))
        customer = get_customer_with_orders_and_details(customer_key)
        self.response.write("Customer: %s<br>" % customer.name)
        for order in customer.orders:
            self.response.write(" Order: %s (" % order.key.id())
            for detail in order.orderdetails:
                self.response.write("%d of %s, " %(detail.quantity, detail.product.name) )
            self.response.write(")<br>")
        self.response.write("<a href='/'>Return to Start</a>")
class A1QueryRequestHandler(webapp2.RequestHandler):
    def get(self, id):
        impl = None
        if self.request.get('impl', '')=='basic':
            from graphfetch import basic_graphfetch
            impl = basic_graphfetch.fetch_basic            
            
        a1=testmodels.get_a1(long(id), impl=impl)
        self.response.write((", ".join((o.name) for o in a1.b1s)) + "<br>")
        self.response.write((", ".join((o.name) for o in a1.b2s)) + "<br>")
        self.response.write((", ".join((o.name) for o in a1.b3s)) + "<br>")
        self.response.write((", ".join((o.name) for o in a1.b4s)) + "<br>")
        self.response.write((", ".join((o.name) for o in a1.b5s)) + "<br>")
        
        if a1.c1: self.response.write(a1.c1.name + "<br>")
        if a1.c2: self.response.write(a1.c2.name + "<br>")
        if a1.c3: self.response.write(a1.c3.name + "<br>")
        if a1.c4: self.response.write(a1.c4.name + "<br>")
        if a1.c5: self.response.write(a1.c5.name + "<br>")

        self.response.write((", ".join((o.name) for o in a1.d1s)) + "<br>")
        self.response.write((", ".join((o.name) for o in a1.d2s)) + "<br>")
        self.response.write((", ".join((o.name) for o in a1.d3s)) + "<br>")
        self.response.write((", ".join((o.name) for o in a1.d4s)) + "<br>")
        self.response.write((", ".join((o.name) for o in a1.d5s)) + "<br>")
        self.response.write("<a href='/'>Return to Start</a>")
class CreateRequestHandler(webapp2.RequestHandler):
    def get(self):
        orders.create_order_test_data()
        testmodels.populate_test_data()
        self.redirect('/')

class HomeRequestHandler(webapp2.RequestHandler):
    def get(self):
        template_values={
                         'customers' : Customer.query().fetch(),
                         'a1s' : testmodels.A1.query().fetch(),
                         }
        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(template_values))

class AssertionsRequestHandler(webapp2.RequestHandler):
    def asert_same(self, actual, expected, label):
        if actual==expected:
            self.response.write("")

    def assert_list_empty(self, list):
        if len(list) > 0:
            self.response.write("List Length")

    def get(self):
        full_a1 = testmodels.A1.query(testmodels.A1.name=="Full Graph").fetch()
        if full_a1:
            full_a1=full_a1[0]
        else:
            self.response.write("no A1 with name 'Full Graph' found - have you populated the database?")
        a1=testmodels.get_a1(full_a1.key.id())
        
        
        self.response.write("<a href='/'>Return to Start</a>")

class FlushMemcacheHandler(webapp2.RequestHandler):
    def get(self):
        memcache.flush_all()
        self.redirect('/')

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
        
app = webapp2.WSGIApplication([
           RedirectRoute('/', HomeRequestHandler, name='home', strict_slash=True),
           RedirectRoute('/flush/', FlushMemcacheHandler, name='flush', strict_slash=True),
           RedirectRoute('/create/', CreateRequestHandler, name='create', strict_slash=True),
           RedirectRoute('/assertions/', AssertionsRequestHandler, name='create', strict_slash=True),
           RedirectRoute('/query/<customer_id>', QueryRequestHandler, name='query', strict_slash=True),
           RedirectRoute('/querya1/<id>', A1QueryRequestHandler, name='query-a1', strict_slash=True),
])







