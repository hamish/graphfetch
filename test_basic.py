import os
import sys
import unittest
import types
import logging
from graphfetch import fetch, FetchDefinition
import testmodels
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
        global Foo
        class Foo(ndb.Model):
            name = ndb.StringProperty()
            rate = ndb.IntegerProperty()
            tags = ndb.StringProperty(repeated=True)
        self.create_entities()
        testmodels.populate_test_data()
        
    def tearDown(self):
        self.testbed.deactivate()
        
    def create_entities(self):
        self.joe = Foo(name='joe', tags=['joe', 'jill', 'hello'], rate=1)
        self.joe.put()
        self.jill = Foo(name='jill', tags=['jack', 'jill'], rate=2)
        self.jill.put()
        self.moe = Foo(name='moe', rate=1)
        self.moe.put()

class BasicFetchTests(GraphFetchTests):

    def testBasicQuery(self):
        fd = FetchDefinition(Foo)
        foo = fetch(fd, key_filter=Foo.name=='joe')[0]
        self.assertEqual(foo.name, 'joe', "name incorrect")

    def testBasicKeyList(self):
        fd = FetchDefinition(Foo)
        foo = fetch(fd, key_filter=Foo.name=='joe')[0]
        self.assertEqual(foo.name, 'joe', "name incorrect")

    def testFullGraph(self):
        fd=testmodels.get_a1_fullfetchdef()
        filter=testmodels.A1.name=='Full Graph'
        results=fetch(fd, key_filter=filter)
        self.assertTrue(isinstance(results, types.ListType), "results should be a list")
        self.assertEqual(len(results), 1, "too many results")
        a1=results[0]
        self.assertTrue(isinstance(a1.b1s, types.ListType), "a1.b1s is not a list")
        self.assertFalse(isinstance(a1.c1, types.ListType), "a1.c1 is not a list")
        self.assertTrue(isinstance(a1.d1s, types.ListType), "a1.d1s is not a list")
        
