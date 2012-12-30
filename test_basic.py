import os
import sys
import unittest
import logging
from graphfetch import fetch, FetchDefinition

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
        
    def tearDown(self):
        self.testbed.deactivate()
        
    def create_entities(self):
        self.joe = Foo(name='joe', tags=['joe', 'jill', 'hello'], rate=1)
        self.joe.put()
        self.jill = Foo(name='jill', tags=['jack', 'jill'], rate=2)
        self.jill.put()
        self.moe = Foo(name='moe', rate=1)
        self.moe.put()

    def testBasicQuery(self):
        fd = FetchDefinition(Foo)
        foo = fetch(fd, key_filter=Foo.name=='joe')[0]
        self.assertEqual(foo.name, 'joe', "name incorrect")

    def testBasicKeyList(self):
        
        fd = FetchDefinition(Foo)
        foo = fetch(fd, key_filter=Foo.name=='joe')[0]
        self.assertEqual(foo.name, 'joe', "name incorrect")
#
#if __name__ == '__main__':
#    # Add the appengine sdk to the python path. Note that this is very specific to my machine (a mac)
#    dev_appserver = '/usr/local/bin/dev_appserver.py'
#    dev_appserver_realpath = os.path.realpath(dev_appserver)
#    dev_appserver_realdir = os.path.split(dev_appserver_realpath)[0]
#    logging.info("adding path: %s" % dev_appserver_realdir)
#    sys.path.append(dev_appserver_realdir)
#    sys.path.append("%s/%s" % (dev_appserver_realdir , 'yaml/lib'))
#    
#    
#    unittest.main()

