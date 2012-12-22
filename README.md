graphfetch
==========

Allows appengine python programmers to retrieve a graph of related objects. The current 
implementation uses the ndb async methods to attempt to do as much work in parallel as possible.


Imagine the following Models

	class Invoice(ndb.Model):
	    line_keys = ndb.KeyProperty(repeated=True)
	    customer_key = ndb.KeyProperty()
	    invoice_number=model.StringProperty()
	
	class Instruction(ndb.Model):
	    invoice_key=ndb.KeyProperty()
	    text = ndb.TextProperty()
	
	class Customer(ndb.Model):
	    name=ndb.StringProperty()
	
	class Line(ndb.Model):
	    item=ndb.KeyProperty()
	    quantity=ndb.IntergerProperty()
	
	class Item(ndb.Model):
	    name=ndb.KeyProperty()
	    tag_keys = ndb.KeyProperty(repeated=True)

Assume for the moment that there is a good reason to have InvoiceLines and Instructions as separate 
entities, and not repeated StructuredPropertys on Invoice.

My goal is to be able to retrieve an invoice and also all associated objects, such that the
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

To implement get_invoice I have defined a couple of different types of relationship between classes. These are:

SOURCE_LIST: keys are stored in a repeated key property on the parent (source) object in the relationship. eg, line_keys on Invoice
SOURCE_KEY: a single key is stored on the source object. eg customer_key on Invoice
TARGET_KEY: a single key is stored on the target object. This is the more standard pattern in relational databases where repeated properties are not commonly used. eg invoice_key on Instruction.

I have also create a class called Fetch that represents the kind of the object to be fetched, and a way to attach new fetches to existing ones.
class Fetch():
    def __init__(self, kind):
        self.kind = kind
    def attach(self, kind, attachment_type, name=None, key_name=None, additional_filter=None):
        ...
        return child_fetch

get_invoice would look something like this:
def get_invoice(invoice_id):
	invoice_fetch = Fetch(kind=Invoice)
	invoice_fetch.attach(kind=Customer, attachment_type=SOURCE_KEY)
	invoice_fetch.attach(kind=Instruction, attachment_TYPE=TARGET_KEY)
	line_fetch = invoice_fetch.attach(kind=Line, attachment_type=SOURCE_LIST)
	line_fetch.attach(kind=Item, attachment_type=SOURCE_KEY)
	return get_graph(invoice_fetch, 

