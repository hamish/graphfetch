graphfetch
==========

Allows appengine python programmers to retrieve a graph of related objects. The current 
implementation uses the ndb async methods to attempt to do as much work in parallel as possible.

Graphfetch allows the source model to be linked to the target model in 3 possible ways:

SOURCE_LIST
==========
Keys are stored in a repeated key property on the parent (source) object in the relationship. 
    class Source(ndb.Model):
    	target_keys=ndb.KeyProperty(kind=Target, repeated=True)
    
    class Target(ndb.Model):
    	pass

A nieve implementation of this attachemnt would be source.targets = ndb.get_multi(source.target_keys)

SOURCE_KEY
==========
A single key is stored on the source object.

    class Source(ndb.Model):
    	target_key=ndb.KeyProperty(kind=Target)
    
    class Target(ndb.Model):
    	pass

A nieve implementation of this attachemnt would be source.target = source.target_key.get()

TARGET_KEY
==========
A single key is stored on the target object. This is the more standard pattern in relational databases where repeated properties are not commonly used. eg invoice_key on Instruction.

    class Source(ndb.Model):
    	pass
    
    class Target(ndb.Model):
    	source_key=ndb.KeyProperty(kind=Target)

A nieve implementation of this attachemnt would be source.targets = Target.query(Target.source_key==source.key).fetch()

An Example:
Imagine the following Models

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
	

Assume for the moment that there is a good reason to have InvoiceLines and Instructions as separate 
entities, and not repeated StructuredPropertys on Invoice.

The goal is to be able to retrieve an invoice and also all associated objects, such that the
following code works:

	invoice = get_invoice(invoice_number)
	print "Invoice: %s" % invoice.invoice_number
	print "Customer: %s" % invoice.customer.name
	for line in invoice.lines:
	    print "%d items of %s: %(line.quantity, line.item.name)
	if invoice.instructions:
	    print "Instructions:"
		for instruction in invoice.instructions:
		    print "%s\n" % instruction.text

In order to define what objects to Retrieve, it is necessisary to create a Fetch graph. The implementaion of Fetch looks a bit like this:

	class Fetch():
	    def __init__(self, kind):
	        self.kind = kind
	    def attach(self, kind, attachment_type, name=None, key_name=None, additional_filter=None):
	        ...
	        return child_fetch

The completed get_invoice method looks like this:
	def get_invoice(invoice_id):
		invoice_fetch = Fetch(kind=Invoice)
		invoice_fetch.attach(kind=Customer, attachment_type=SOURCE_KEY)
		invoice_fetch.attach(kind=Instruction, attachment_TYPE=TARGET_KEY)
		line_fetch = invoice_fetch.attach(kind=Line, attachment_type=SOURCE_LIST)
		line_fetch.attach(kind=Item, attachment_type=SOURCE_KEY)
		return get_graph(invoice_fetch, 

