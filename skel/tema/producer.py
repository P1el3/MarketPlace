"""
This module represents the Producer.

Computer Systems Architecture Course
Assignment 1
March 2021
"""
from time import sleep
from threading import Thread


class Producer(Thread):
    """
    Class that represents a producer.
    """

    def __init__(self, products, marketplace, republish_wait_time, **kwargs):
        """
        Constructor.

        @type products: List()
        @param products: a list of products that the producer will produce

        @type marketplace: Marketplace
        @param marketplace: a reference to the marketplace

        @type republish_wait_time: Time
        @param republish_wait_time: the number of seconds that a producer must
        wait until the marketplace becomes available

        @type kwargs:
        @param kwargs: other arguments that are passed to the Thread's __init__()
        """
        Thread.__init__(self, **kwargs)
        self.products = products
        self.marketplace = marketplace
        self.republish_wait_time = republish_wait_time
        self.kwargs = kwargs

    def run(self):
        producer_id = self.marketplace.register_producer()

        while True:
            product_index = 0

            while product_index < len(self.products):
                (product, product_qty, waiting_time) = self.products[product_index]
                sleep(waiting_time)

                for _ in range(product_qty):
                    while self.marketplace.publish(str(producer_id), product) is False:
                        sleep(self.republish_wait_time)
                product_index += 1
