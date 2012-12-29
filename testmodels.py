import logging
from google.appengine.ext import ndb
import graphfetch


# A-D a broad model - A has 5 children of each type:
# B[1-5] is SOURCE_LIST, C[1-5] is SOURCE_KEY, D[1-5] is TARGET_KEY
class A1(ndb.Model):
    name=ndb.StringProperty()
    b1_keys=ndb.KeyProperty(repeated=True)
    b2_keys=ndb.KeyProperty(repeated=True)
    b3_keys=ndb.KeyProperty(repeated=True)
    b4_keys=ndb.KeyProperty(repeated=True)
    b5_keys=ndb.KeyProperty(repeated=True)
    c1_key=ndb.KeyProperty()
    c2_key=ndb.KeyProperty()
    c3_key=ndb.KeyProperty()
    c4_key=ndb.KeyProperty()
    c5_key=ndb.KeyProperty()
    
class B1(ndb.Model):
    name=ndb.StringProperty()
class B2(ndb.Model):
    name=ndb.StringProperty()
class B3(ndb.Model):
    name=ndb.StringProperty()
class B4(ndb.Model):
    name=ndb.StringProperty()
class B5(ndb.Model):
    name=ndb.StringProperty()
class C1(ndb.Model):
    name=ndb.StringProperty()
class C2(ndb.Model):
    name=ndb.StringProperty()
class C3(ndb.Model):
    name=ndb.StringProperty()
class C4(ndb.Model):
    name=ndb.StringProperty()
class C5(ndb.Model):
    name=ndb.StringProperty()
class D1(ndb.Model):
    a1_key=ndb.KeyProperty()
    name=ndb.StringProperty()
class D2(ndb.Model):
    a1_key=ndb.KeyProperty()
    name=ndb.StringProperty()
class D3(ndb.Model):
    a1_key=ndb.KeyProperty()
    name=ndb.StringProperty()
class D4(ndb.Model):
    a1_key=ndb.KeyProperty()
    name=ndb.StringProperty()
class D5(ndb.Model):
    a1_key=ndb.KeyProperty()
    name=ndb.StringProperty()

def get_a1_fullfetchdef():
    a1_fd=graphfetch.FetchDefinition(A1)
    a1_fd.attach(kind=B1, attachment_type=graphfetch.SOURCE_LIST)
    a1_fd.attach(kind=B2, attachment_type=graphfetch.SOURCE_LIST)
    a1_fd.attach(kind=B3, attachment_type=graphfetch.SOURCE_LIST)
    a1_fd.attach(kind=B4, attachment_type=graphfetch.SOURCE_LIST)
    a1_fd.attach(kind=B5, attachment_type=graphfetch.SOURCE_LIST)
    a1_fd.attach(kind=C1, attachment_type=graphfetch.SOURCE_KEY)
    a1_fd.attach(kind=C2, attachment_type=graphfetch.SOURCE_KEY)
    a1_fd.attach(kind=C3, attachment_type=graphfetch.SOURCE_KEY)
    a1_fd.attach(kind=C4, attachment_type=graphfetch.SOURCE_KEY)
    a1_fd.attach(kind=C5, attachment_type=graphfetch.SOURCE_KEY)
    a1_fd.attach(kind=D1, attachment_type=graphfetch.TARGET_KEY, order=D1.name)
    a1_fd.attach(kind=D2, attachment_type=graphfetch.TARGET_KEY, order=D1.name)
    a1_fd.attach(kind=D3, attachment_type=graphfetch.TARGET_KEY, order=D1.name)
    a1_fd.attach(kind=D4, attachment_type=graphfetch.TARGET_KEY, order=D1.name)
    a1_fd.attach(kind=D5, attachment_type=graphfetch.TARGET_KEY, order=-D1.name)
    return a1_fd

def get_a1_by_key(id):
    a1_fd = get_a1_fullfetchdef()
    key=ndb.Key(A1,id)
    return graphfetch.fetch(a1_fd, keys=key)

def get_a1(id):
    a1_fd = get_a1_fullfetchdef()
    key=ndb.Key(A1,long(id))
    key_filter = A1.key == key
    logging.info(key_filter)
    return graphfetch.fetch(a1_fd, key_filter=key_filter)[0]
    

def populate_test_data():
    #Create 5 of all B and C classes
    to_put = []
    for i in range(5):
        to_put.append(B1(name="B1_%d" % i))
        to_put.append(B2(name="B2_%d" % i))
        to_put.append(B3(name="B3_%d" % i))
        to_put.append(B4(name="B4_%d" % i))
        to_put.append(B5(name="B5_%d" % i))
    to_put.append(C1(name="C1" ))
    to_put.append(C2(name="C2" ))
    to_put.append(C3(name="C3" ))
    to_put.append(C4(name="C4" ))
    to_put.append(C5(name="C5" ))
    child_objs = ndb.put_multi(to_put)
    # create an A1
    a1 = A1(name="Full Graph")
    for i in range(5):
        a1.b1_keys.append(child_objs.pop(0))
        a1.b2_keys.append(child_objs.pop(0))
        a1.b3_keys.append(child_objs.pop(0))
        a1.b4_keys.append(child_objs.pop(0))
        a1.b5_keys.append(child_objs.pop(0))
    a1.c1_key=child_objs.pop(0)
    a1.c2_key=child_objs.pop(0)
    a1.c3_key=child_objs.pop(0)
    a1.c4_key=child_objs.pop(0)
    a1.c5_key=child_objs.pop(0)
    a1.put()
    # create the D objects
    to_put=[]
    for i in range(5):
        to_put.append(D1(name="D1_%d" % i, a1_key=a1.key))
        to_put.append(D2(name="D2_%d" % i, a1_key=a1.key))
        to_put.append(D3(name="D3_%d" % i, a1_key=a1.key))
        to_put.append(D4(name="D4_%d" % i, a1_key=a1.key))
        to_put.append(D5(name="D5_%d" % i, a1_key=a1.key))
    ndb.put_multi(to_put)
    
    a1=A1(name="Empty Graph")
    a1.put()
