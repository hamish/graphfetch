# Graphfetch

Allows appengine python programmers to retrieve a set of related ndb datastore objects, connected together into a graph for easy 

## Background
When I first started using ndb, I found myself doing things like invoice.customer.get().name in my template code. This seemed to be a bad idea(tm).

I started creating custom code to manually stitch results together, this worked a lot better - particularly in the templates, but I ended up with a lot more code to maintain than I wanted. This is also when I developed the pattern of using identifier_key for KeyProperties and identifier_keys for repeated Key Properties so that identifier and identifiers were available on the object to attache the target objects and lists.

In an effort to reduce the amount of code I have to support, I have consolidated the code that retrieves datastore objects into the graphfetch library. It allows the user to specify what child (or target) objects should also be available when a top level object is retrieved.


## Overview
To use graphfetch, 

1. Construct the FetchDefinition graph which defines what objects should be retreived.
2. call fetch with the fetch definition and either the keys of the objects to retrieve, or the filter to use with a query.

The current implementation uses the ndb async methods to attempt to do as much work in parallel as possible, reducing the elapsed time to fetch the objects. 

## Attachment Types
Graphfetch allows the source model to be linked to the target model in 3 possible ways:

### SOURCE_LIST
Keys are stored in a repeated key property on the parent (source) object in the relationship. Results in a list being attached to the source object.
```python
class Source(ndb.Model):
	target_keys=ndb.KeyProperty(kind=Target, repeated=True)

class Target(ndb.Model):
	pass
```
A naive implementation of this attachment would be source.targets = ndb.get_multi(source.target_keys)

### SOURCE_KEY
A single key is stored on the source object. Results in a single object (or None) being attached to the source object.

```python
class Source(ndb.Model):
	target_key=ndb.KeyProperty(kind=Target)

class Target(ndb.Model):
	pass
```

A naive implementation of this attachment would be source.target = source.target_key.get()

### TARGET_KEY
A single key is stored on the target object. This is the more standard pattern in relational databases where repeated properties are not commonly used. Results in a list being attached to the source object.

```python
class Source(ndb.Model):
	pass

class Target(ndb.Model):
	source_key=ndb.KeyProperty(kind=Target)
```

A naive implementation of this attachment would be source.targets = Target.query(Target.source_key==source.key).fetch()

## FetchDefinition Graph
The fetch definition graph defines the objects that should be retrieved. The interface is as follows.
```python
class FetchDefinition():
    def __init__(self, kind):
        self.kind = kind
    def attach(self, kind, attachment_type, name=None, key_name=None, additional_filter=None, order=None):
    	child_fd=FetchDefinition(...)
        ...
        return child_fd
```
The usual pattern is to create a fetch definition, and then use the attach method to create and attach child fetch definitions. The child fetch definitions are returned from the attach method so that they can also have child fetch definitions.

The parameter meanings are:
* kind: The class of the child object being attached
* attachment_type: One of SOURCE_LIST, SOURCE_KEY or TARGET_KEY
* name: The name of the attribute on the parent object to attache the child object to.
* key_name: The name of the data model attribute to be used to locate the child object.
* additional_filter: ndb filter that can further restrict the objects attached. This is only used with TARGET_KEY attachments.
* order: The attribute on target to order the results by. This is only used with TARGET_KEY attachments.

#### Default Values
* name: Defaults to target_kind.lower() or target_kind.lower() + 's' if the attachment results in a list.
* key_name: Defaults to target_kind.lower + '_key' for SOURCE_KEY, source_kind.lower() ='_key' for  TARGET_KEY and target_kind.lower() = '_keys' for SOURCE_KEY Attachments. 
eg:
```python
fd = FetchDefinition(Source)
fd.attach(Target, SOURCE_LIST)
```
name would default to 'targets' and key_name would default to 'target_keys'
```python
fd.attach(Target, SOURCE_KEY)
```
name would default to 'target' and key_name would default to 'target_key'
```python
fd.attach(Target, TARGET_KEY)
```
name would default to 'targets' and key_name would default to 'source_key'

## fetch
The final stage is to call the fetch method. 
```python
def fetch(fetch_definition, future=None, keys=None, key_filter=None, additional_filter=None, order=None):
```
* fetch_definition: the top level fetch object
* future: Not generally used externally. The result of an async ndb method. 
* keys: A Key or list of Keys that represent the top level object(s).
* key_filter: An ndb filter that will select the top level object(s).
* additional_filter: Not generally used externally. Additional filter to be applied to the query.
* order: The attribute to order the results by. Only used with query style (key_filter) methods. 

keys, key_filter and future are mutually exclusive.

## An Example:
Imagine the following Models

```python
class Instruction(ndb.Model):
    invoice_key=ndb.KeyProperty(kind=Invoice)
    text = ndb.TextProperty()

class Invoice(ndb.Model):
    line_keys = ndb.KeyProperty(kind=Line, repeated=True)
    customer_key = ndb.KeyProperty(kind=Customer)
    invoice_number=model.StringProperty()	

class Customer(ndb.Model):
    name=ndb.StringProperty()

class Item(ndb.Model):
    name=ndb.KeyProperty()

class Line(ndb.Model):
    item=ndb.KeyProperty(kind=Item)
    quantity=ndb.IntergerProperty()
```
Assume for the moment that there is a good reason to have a datamodel that looks like this (I can't think of one.)

The goal is to be able to retrieve an invoice and also all associated objects, such that the
following code works:

```python
invoice = get_invoice(invoice_number)
print "Invoice: %s" % invoice.invoice_number
print "Customer: %s" % invoice.customer.name
for line in invoice.lines:
    print "%d items of %s: %(line.quantity, line.item.name)
if invoice.instructions:
    print "Instructions:"
	for instruction in invoice.instructions:
	    print "%s\n" % instruction.text
```

Create a fetch graph and call fetch.
```python
def get_invoice(invoice_id):
	invoice_fetch = FetchDefinition(kind=Invoice)
	invoice_fetch.attach(kind=Customer, attachment_type=SOURCE_KEY)
	invoice_fetch.attach(kind=Instruction, attachment_TYPE=TARGET_KEY)
	line_fetch = invoice_fetch.attach(kind=Line, attachment_type=SOURCE_LIST)
	line_fetch.attach(kind=Item, attachment_type=SOURCE_KEY)
	key=ndb.Key(Invoice, invoice_id)
	return fetch(invoice_fetch, keys)
```


## Performance 

Graphfetch uses the ndb async methods to execute as much of the datastore activity in parallel as possible. Performance appears to be very good. A future enhancement #1 aims to provide a tasklet based implementation which may be faster in some complex situations.

graphfetch does not set aside the need for thoughtful data model design. 

## Issues
Please report any issues that you find in github.

## Future work

* Comprehensive testing
* Performance improvements
* Pagination for top level fetches



