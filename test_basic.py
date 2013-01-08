import os
import sys
import unittest
import types
import logging
from graphfetch import fetch, fetch_page, FetchDefinition, SOURCE_LIST, SOURCE_KEY, TARGET_KEY
import testmodels, orders
from google.appengine.ext import ndb

class GraphFetchTests(unittest.TestCase):
    def setUp(self):
        from google.appengine.ext import ndb
        from google.appengine.datastore import datastore_stub_util
        from google.appengine.ext import testbed
        
        # activate GAE stubs
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_taskqueue_stub()
        self.testbed.init_mail_stub()
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)
        self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
        self.testbed.init_user_stub()

        self.headers = {'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) Version/6.0 Safari/536.25',
                        'Accept-Language' : 'en_US'}
        
    def tearDown(self):
        self.testbed.deactivate()
        


class BasicFetchTests(GraphFetchTests):
    def setUp(self):
        super(BasicFetchTests, self).setUp()
        
        global Foo
        class Foo(ndb.Model):
            name = ndb.StringProperty()
            rate = ndb.IntegerProperty()
            tags = ndb.StringProperty(repeated=True)
        self.create_entities()
        #testmodels.populate_test_data()
        
    def create_entities(self):
        self.joe = Foo(id=101, name='joe', tags=['joe', 'jill', 'hello'], rate=1)
        self.joe.put()
        self.jill = Foo(id=102, name='jill', tags=['jack', 'jill'], rate=2)
        self.jill.put()
        self.moe = Foo(id=103, name='moe', rate=1)
        self.moe.put()

    def assertJoe(self, obj):
        self.assertEqual(obj.name, 'joe', "name incorrect")
        self.assertEqual(obj.id, obj.key.id(), "foo.id should be set to the value of foo.key.id(). Is transform_model working?")
        
    def testKeysQuery(self):
        fd = FetchDefinition(Foo)
        key = ndb.Key(Foo, 101)
        foo = fetch(fd, keys=[key])[0]
        self.assertJoe(foo)

    def testKeyQuery(self):
        fd = FetchDefinition(Foo)
        key = ndb.Key(Foo, 101)
        foo = fetch(fd, key=key)
        self.assertJoe(foo)

    def testBasicQuery(self):
        fd = FetchDefinition(Foo)
        foo = fetch(fd, filter=Foo.name=='joe')[0]
        self.assertJoe(foo)

    def testQueryAll(self):
        fd = FetchDefinition(Foo)
        results = fetch(fd)
        self.assertEqual(len(results), 3, "Querying with no keys, future or filter should return all entities")

    def testQueryNoResults(self):
        fd = FetchDefinition(Foo)
        results = fetch(fd, filter=Foo.name=='NOTHING MATCHES THIS')
        self.assertTrue(len(results)==0, "non empty results returned")

        results2, curs, more = fetch_page(fd, 10, filter=Foo.name=='NOTHING MATCHES THIS')
        self.assertTrue(len(results2)==0, "non empty results returned")

    def testBasicKeyList(self):
        fd = FetchDefinition(Foo)
        foo = fetch(fd, filter=Foo.name=='joe')[0]
        self.assertEqual(foo.name, 'joe', "name incorrect")

class FullGraphFetchTests(GraphFetchTests):
    def setUp(self):
        super(FullGraphFetchTests, self).setUp()
        testmodels.populate_test_data()
        

    def assertAllAreType(self, o, names, type):
        for name in names:
            val = getattr(o,name)
            self.assertTrue(isinstance(val, type), "attribute %s is not %s" %(name, type))
    def assertAllAreLength(self, o, names, length):
        for name in names:
            val = getattr(o,name)
            val_len = len(val)
            self.assertTrue(val_len == length, "attribute %s length is %d  not %d" %(name, val_len, length))

    def assertFullGraphResults(self, results):
        self.assertTrue(isinstance(results, types.ListType), "results should be a list")
        self.assertEqual(len(results), 1, "too many results")
        a1=results[0]

        b_names = ["b%ds"%i for i in range(1,6)]
        self.assertAllAreType(a1, b_names, types.ListType)
        self.assertAllAreLength(a1, b_names, 5)

        c_names = ["c%d"%i for i in range(1,6)]
        self.assertAllAreType(a1, c_names, ndb.Model)
        # c attributes have no length - so no assertAllAreLength

        d_names = ["d%ds"%i for i in range(1,6)]
        self.assertAllAreType(a1, d_names, types.ListType)
        self.assertAllAreLength(a1, d_names, 5)
                
    def testFullGraph(self):
        fd=testmodels.get_a1_fullfetchdef()
        filter=testmodels.A1.name=='Full Graph'
        results=fetch(fd, filter=filter)
        self.assertFullGraphResults(results)
    
    def testFullGraphBasicImpl(self):
        from graphfetch import basic_graphfetch
        fd=testmodels.get_a1_fullfetchdef()
        filter=testmodels.A1.name=='Full Graph'
        results=fetch(fd, filter=filter, impl=basic_graphfetch.fetch_basic)
        self.assertFullGraphResults(results)

    def testCustomTransformMoodel(self):
        def custom_transform(o):
            o.testattr=True
            return o
        fd=testmodels.get_a1_fullfetchdef()
        filter=testmodels.A1.name=='Full Graph'
        results=fetch(fd, filter=filter, transform=custom_transform)
        
        a1=results[0]
        self.assertTrue(a1.testattr, "testattr should be set to true by custom_transform")
        self.assertFalse(hasattr(a1,'id'), "id attribute has been set even though the custom transform was used.")

        # also test for models deeper in the graph
        self.assertTrue(a1.b1s[0].testattr, "testattr should be set to true by custom_transform")
        self.assertFalse(hasattr(a1.b1s[0],'id'), "id attribute has been set even though the custom transform was used.")

        self.assertTrue(a1.c1.testattr, "testattr should be set to true by custom_transform")
        self.assertFalse(hasattr(a1.c1,'id'), "id attribute has been set even though the custom transform was used.")

        self.assertTrue(a1.d1s[0].testattr, "testattr should be set to true by custom_transform")
        self.assertFalse(hasattr(a1.d1s[0],'id'), "id attribute has been set even though the custom transform was used.")

class SortTests(GraphFetchTests):
    def setUp(self):
        super(SortTests, self).setUp()
        global Source, Target
        class Source(ndb.Model):
            name = ndb.StringProperty()
            target_keys = ndb.KeyProperty(repeated=True)
        class Target(ndb.Model):
            name=ndb.StringProperty()
            order=ndb.IntegerProperty()
        self.create_entities()
        #testmodels.populate_test_data()
        
    def create_entities(self):
        self.t1 = Target(id=1, name='t1', order=1)
        self.t1.put()
        self.t2 = Target(id=2, name='t2', order=2)
        self.t2.put()
        self.t3 = Target(id=3, name='t3', order=3)
        self.t3.put()
        
        self.source = Source(id=100, name='source', target_keys=[self.t2.key, self.t1.key, self.t3.key])
        self.source.put()

    def testSortKeyBasicImpl(self):
        from graphfetch import basic_graphfetch
        fd = FetchDefinition(testmodels.A1)
        fd.attach(kind=Target, attachment_type=SOURCE_LIST, sort_key=lambda elem: elem.order)
        key=ndb.Key(Source, 100)
        s1=fetch(fd, key=key, impl=basic_graphfetch.fetch_basic)
        self.assertEqual(s1.targets[0].name, 't1')
    
    def testSortKey(self):
        from graphfetch import basic_graphfetch
        fd = FetchDefinition(testmodels.A1)
        fd.attach(kind=Target, attachment_type=SOURCE_LIST, sort_key=lambda elem: elem.order)
        key=ndb.Key(Source, 100)
        s1=fetch(fd, key=key)
        self.assertEqual(s1.targets[0].name, 't1')

class OrderGraphFetchTests(GraphFetchTests):
    def setUp(self):
        super(OrderGraphFetchTests, self).setUp()
        orders.create_order_test_data()
    def testSetup(self):
        fd=orders.get_full_order_fetchdef()
        filter=orders.Customer.account_id>=-1
        values = fetch(fd, filter=filter)
        customer=values[0]
        self.assertTrue(isinstance(customer.orders, types.ListType), "Customer.orders should be a list")
        
    def testPagination(self):
        fd=orders.get_full_order_fetchdef()
        filter=orders.Customer.account_id>=-1 # This selects all records - in future allow None filter to do this.
        
        # Page 1
        results1, curs1, more1=fetch_page(fd, 6, filter=filter, order=orders.Customer.account_id)
        self.assertEqual(len(results1), 6)
        customer=results1[0]
        curs1_str=curs1.urlsafe()
        self.assertTrue(isinstance(customer.orders, types.ListType), "Customer.orders should be a list")
        
        # Page 2
        new_curs1 = ndb.Cursor(urlsafe=curs1_str)
        results2, curs2, more2=fetch_page(fd, 6, filter=filter, start_cursor=new_curs1, order=orders.Customer.account_id)
        self.assertEqual(len(results2), 4)
        self.assertFalse(more2)
        
        # Page 3 should be the same as page 1, except with the results in the opposite order.
        prev_cursor=new_curs1.reversed()
        results3, curs3, more3=fetch_page(fd, 6, filter=filter, start_cursor=prev_cursor, order=-orders.Customer.account_id)
        results3.reverse()

        self.assertEqual(results3[0].key.id(), results1[0].key.id())

        # Page 4 is the page after Page 2 (should have no results)
        results4, curs4, more4=fetch_page(fd, 6, filter=filter, start_cursor=curs2, order=orders.Customer.account_id)
        

