"""
This module represents the Consumer.

Computer Systems Architecture Course
Assignment 1
March 2021
"""
from threading import Thread
from time import sleep

ADD_OP = "add"
REMOVE_OP = "remove"
PRINT_LOCK = 3
class Consumer(Thread):
    """
    Class that represents a consumer.
    """

    def __init__(self, carts, marketplace, retry_wait_time, **kwargs):
        """
        Constructor.

        :type carts: List
        :param carts: a list of add and remove oprs

        :type marketplace: Marketplace
        :param marketplace: a reference to the marketplace

        :type retry_wait_time: Time
        :param retry_wait_time: the number of seconds that a producer must wait
        until the Marketplace becomes available

        :type kwargs:
        :param kwargs: other arguments that are passed to the Thread's __init__()
        """
        Thread.__init__(self, **kwargs)
        self.carts = carts
        self.marketplace = marketplace
        self.retry_wait_time = retry_wait_time

    def run(self):
        for cart in self.carts:
            cart_id = self.marketplace.new_cart()
            for opr in cart:
                if opr["type"] == ADD_OP:
                    quantity_index = 0
                    while quantity_index < opr["quantity"]:
                        while not self.marketplace.add_to_cart(cart_id, opr["product"]):
                            sleep(self.retry_wait_time)
                        quantity_index += 1
                elif opr["type"] == REMOVE_OP:
                    quantity_index = 0
                    while quantity_index < opr["quantity"]:
                        self.marketplace.remove_from_cart(cart_id, opr["product"])
                        quantity_index += 1

            products = self.marketplace.place_order(cart_id)

            with self.marketplace.locks[3]:
                for product in products:
                    print(f"{self.name} bought {product}")
