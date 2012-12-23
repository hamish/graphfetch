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
import graphfetch
import random
import logging
import testmodels

# Data Model
class Customer(ndb.Model):
    name=ndb.StringProperty()
    
class Product(ndb.Model):
    name=ndb.StringProperty()

class OrderDetail(ndb.Model):
    product_key=ndb.KeyProperty(kind=Product)
    quantity=ndb.IntegerProperty()
    
class Order(ndb.Model):
    customer_key=ndb.KeyProperty(kind=Customer)
    orderdetail_keys=ndb.KeyProperty(kind=OrderDetail, repeated=True)
    
# utility Methods
def get_order(order_key):
    fetch = graphfetch.Fetch(kind=Order)
    fetch.attach(kind=OrderDetail, attachment_type=graphfetch.SOURCE_LIST)

def get_customer_with_orders_and_details(customer_key):
    customer_fetch = graphfetch.Fetch(Customer)
    order_fetch = customer_fetch.attach(Order, graphfetch.TARGET_KEY)
    detail_fetch = order_fetch.attach(OrderDetail, graphfetch.SOURCE_LIST)
    product_fetch = detail_fetch.attach(Product, graphfetch.SOURCE_KEY)
    
    keys=[customer_key]

    customer = graphfetch.get_graph(customer_fetch, keys=keys)[0]
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
        a1=testmodels.get_a1(long(id))
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
        # create test data
        products=[]
        for product_num in range(100):
            name="Product %d" % (product_num)
            product = Product(name=name)
            products.append(product)
        product_keys = ndb.put_multi(products)
        for cust_num in range(10):
            cust = Customer(name="Customer %d" % cust_num)
            cust.put()
            orders=[]
            for order_number in range(5):
                details = []
                for detail_num in range(3):
                    detail = OrderDetail(quantity=random.randint(1,10),
                                         product_key=random.choice(product_keys))
                    details.append(detail)
                orderdetail_keys=ndb.put_multi(details)
                order = Order(customer_key=cust.key, orderdetail_keys=orderdetail_keys)
                orders.append(order)
            ndb.put_multi(orders)
        testmodels.populate_test_data()
        self.redirect('/')

class HomeRequestHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write("<a href='/assertions/'>Assertions</a><br>")
        self.response.write("<a href='/create/'>Create Test Data</a><hr>")
        customers = Customer.query().fetch()
        for customer in customers:
            self.response.write("<a href='/query/%d'>Query Data for customer %s</a><br>" % (customer.key.id(), customer.name))
        a1s = testmodels.A1.query().fetch()
        for a1 in a1s:
            self.response.write("<a href='/querya1/%d'>Query A1: %s<br>" % (a1.key.id(), a1.name))

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
        
app = webapp2.WSGIApplication([
           RedirectRoute('/', HomeRequestHandler, name='home', strict_slash=True),
           RedirectRoute('/create/', CreateRequestHandler, name='create', strict_slash=True),
           RedirectRoute('/assertions/', AssertionsRequestHandler, name='create', strict_slash=True),
           RedirectRoute('/query/<customer_id>', QueryRequestHandler, name='query', strict_slash=True),
           RedirectRoute('/querya1/<id>', A1QueryRequestHandler, name='query-a1', strict_slash=True),
])







