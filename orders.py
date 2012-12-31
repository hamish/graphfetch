from google.appengine.ext import ndb
import random
import graphfetch

# Data Model
class Customer(ndb.Model):
    name=ndb.StringProperty()
    account_id=ndb.IntegerProperty()
    
class Product(ndb.Model):
    name=ndb.StringProperty()

class OrderDetail(ndb.Model):
    product_key=ndb.KeyProperty(kind=Product)
    quantity=ndb.IntegerProperty()
    
class Order(ndb.Model):
    customer_key=ndb.KeyProperty(kind=Customer)
    orderdetail_keys=ndb.KeyProperty(kind=OrderDetail, repeated=True)

def get_full_order_fetchdef():
    customer_fetch = graphfetch.FetchDefinition(Customer)
    order_fetch = customer_fetch.attach(Order, graphfetch.TARGET_KEY)
    detail_fetch = order_fetch.attach(OrderDetail, graphfetch.SOURCE_LIST)
    product_fetch = detail_fetch.attach(Product, graphfetch.SOURCE_KEY)
    return customer_fetch
    
def create_order_test_data():
    # create test data
    products=[]
    for product_num in range(100):
        name="Product %d" % (product_num)
        product = Product(name=name)
        products.append(product)
    product_keys = ndb.put_multi(products)
    for cust_num in range(10):
        cust = Customer(name="Customer %d" % cust_num, account_id=cust_num)
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
