from google.appengine.ext import ndb
from graphfetch import SOURCE_KEY, SOURCE_LIST, TARGET_KEY, FetchDefinition, get_graph
class Invoice(ndb.Model):
    line_keys = ndb.KeyProperty(repeated=True)
    customer_key = ndb.KeyProperty()
    invoice_number=ndb.StringProperty()

class Instruction(ndb.Model):
    invoice_key=ndb.KeyProperty()
    text = ndb.TextProperty()

class Customer(ndb.Model):
    name=ndb.StringProperty()

class Line(ndb.Model):
    item=ndb.KeyProperty()
    quantity=ndb.IntegerProperty()

class Item(ndb.Model):
    name=ndb.KeyProperty()
    tag_keys = ndb.KeyProperty(repeated=True)

def get_invoice(invoice_id):
    invoice_fd = FetchDefinition(kind=Invoice)
    invoice_fd.attach(kind=Customer, attachment_type=SOURCE_KEY)
    invoice_fd.attach(kind=Instruction, attachment_TYPE=TARGET_KEY)
    line_fd = invoice_fd.attach(kind=Line, attachment_type=SOURCE_LIST)
    line_fd.attach(kind=Item, attachment_type=SOURCE_KEY)
    key= ndb.Key(Invoice, invoice_id)
    return get_graph(invoice_fd, keys=key)
                         
def example_code(invoice_id):
    invoice = get_invoice(invoice_id)
    print "Invoice: %s" % invoice.invoice_number
    print "Customer: %s" % invoice.customer.name
    for line in invoice.lines:
        print "%d items of %s" %(line.quantity, line.item.name)
    if invoice.instructions:
        print "Instructions:"
        for instruction in invoice.instructions:
            print "%s\n" % instruction.text

