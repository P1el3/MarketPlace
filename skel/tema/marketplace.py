"""
This module represents the Marketplace.

Computer Systems Architecture Course
Assignment 1
March 2021
"""
import logging
import unittest
import time
from logging.handlers import RotatingFileHandler
from threading import Lock
PROD_LOCK = 0
CONS_LOCK = 1
CART_LOCK = 2
PRINT_LOCK = 3

class TestMarketplace(unittest.TestCase):
    def setUp(self):
        self.marketplace = Marketplace(10)
        self.tea = ('cevaBun', 10, 'CEAI')

    def test_register_producer(self):
        producer_id = self.marketplace.register_producer()
        self.assertEqual(producer_id, 0)
        producer_id = self.marketplace.register_producer()
        self.assertEqual(producer_id, 1)
        producer_id = self.marketplace.register_producer()
        self.assertEqual(producer_id, 2)

    def test_publish(self):
        producer_id = self.marketplace.register_producer()
        self.assertTrue(self.marketplace.publish(producer_id, self.tea))
        self.assertEqual(len(self.marketplace.producer_lists[producer_id]), 1)
        self.assertTrue(self.marketplace.publish(producer_id, self.tea))
        self.assertEqual(len(self.marketplace.producer_lists[producer_id]), 2)
        self.assertFalse(self.marketplace.publish(producer_id + 3, self.tea))

    def test_new_cart(self):
        cart_id = self.marketplace.new_cart()
        self.assertEqual(cart_id, 0)
        cart_id = self.marketplace.new_cart()
        self.assertEqual(cart_id, 1)
        cart_id = self.marketplace.new_cart()
        self.assertEqual(cart_id, 2)

    def test_add_to_cart(self):
        producer_id = self.marketplace.register_producer()
        cart_id = self.marketplace.new_cart()
        self.assertFalse(self.marketplace.add_to_cart(cart_id, self.tea))
        self.assertTrue(self.marketplace.publish(producer_id, self.tea))
        self.assertTrue(self.marketplace.add_to_cart(cart_id, self.tea))

    def test_remove_from_cart(self):
        producer_id = self.marketplace.register_producer()
        cart_id = self.marketplace.new_cart()
        self.assertTrue(self.marketplace.publish(producer_id, self.tea))
        self.assertTrue(self.marketplace.add_to_cart(cart_id, self.tea))
        self.assertEqual(len(self.marketplace.cart_list[cart_id]), 1)
        self.marketplace.remove_from_cart(cart_id, self.tea)
        self.assertEqual(len(self.marketplace.cart_list[cart_id]), 0)

    def test_place_order(self):
        producer_id = self.marketplace.register_producer()
        cart_id = self.marketplace.new_cart()
        self.assertTrue(self.marketplace.publish(producer_id, self.tea))
        self.assertTrue(self.marketplace.add_to_cart(cart_id, self.tea))
        my_l = self.marketplace.place_order(cart_id)
        self.assertEqual(my_l, [('cevaBun', 10, 'CEAI')])

class Marketplace:
    """
    Class that represents the Marketplace. It's the central part of the implementation.
    The producers and consumers use its methods concurrently.
    """
    logging.basicConfig(
                        handlers=[RotatingFileHandler
                                      (
                                        './marketplace.log', maxBytes=100000, backupCount=10
                                      )
                                 ],
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S', level=logging.INFO
                        )
    logging.Formatter.converter = time.gmtime
    logger = logging.getLogger()
    def __init__(self, queue_size_per_producer):
        """
        Constructor

        :type queue_size_per_producer: Int
        :param queue_size_per_producer: the maximum size of a queue associated with each producer
        """

        self.queue_size_per_producer = queue_size_per_producer

        self.last_prod_id = 0
        self.producer_lists = []
        self.producer_list_sizes = []
        self.removed_products = {}

        self.last_cart_id = 0
        self.cart_list = []
        self.cart_list_sizes = []

        self.locks = [Lock(), Lock(), Lock(), Lock()]

    def register_producer(self):
        """
        Returns an id for the producer that calls this.
        """
        with self.locks[PROD_LOCK]:
            self.producer_lists.append([])
            self.producer_list_sizes.append(0)
            self.last_prod_id += 1
            self.logger.info("new producer with id: %d", self.last_prod_id - 1)
        return self.last_prod_id - 1

    def publish(self, producer_id, product):
        """
        Adds the product provided by the producer to the marketplace

        :type producer_id: String
        :param producer_id: producer id

        :type product: Product
        :param product: the Product that will be published in the Marketplace

        :returns True or False. If the caller receives False, it should wait and then try again.
        """
        producer_id = int(producer_id)
        if producer_id >= self.last_prod_id:
            self.logger.info("error, producer id doesn't exist")
            return False

        with self.locks[PROD_LOCK]:
            if len(self.producer_lists[producer_id]) >= self.queue_size_per_producer:
                self.logger.info("error, max que size")
                return False

            self.producer_lists[producer_id].append(product)
            self.producer_list_sizes[producer_id] += 1
            self.logger.info("producer: %d has produced new item: %s", producer_id, product)
        return True

    def new_cart(self):
        """
        Creates a new cart for the consumer

        :returns an int representing the cart_id
        """
        with self.locks[CONS_LOCK]:
            self.cart_list.append([])
            self.cart_list_sizes.append(0)
            self.last_cart_id += 1
            self.logger.info("new cart with id: %d", self.last_cart_id - 1)
        # Return cart's id
        return self.last_cart_id - 1

    def add_to_cart(self, cart_id, product):
        """
        Adds a product to the given cart. The method returns

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to add to cart

        :returns True or False. If the caller receives False, it should wait and then try again
        """
        with self.locks[PROD_LOCK]:
            # Search for the product in the lists of all producers
            for i, prod_list in enumerate(self.producer_lists):
                if product in prod_list:
                    # Remove the product from the producer's list
                    prod_list.remove(product)
                    self.removed_products[i] = product
                    self.producer_list_sizes[i] -= 1

                    with self.locks[CART_LOCK]:
                        # Add the product to the cart
                        self.cart_list[cart_id].append(product)
                        self.cart_list_sizes[cart_id] += 1
                    self.logger.info("product %s in cart %d", product, cart_id)
                    return True

        return False

    def remove_from_cart(self, cart_id, product):
        """
        Removes a product from cart.

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to remove from cart
        """
        with self.locks[CART_LOCK]:
            if product in self.cart_list[cart_id]:
                self.cart_list[cart_id].remove(product)
                self.cart_list_sizes[cart_id] -= 1
                self.logger.info("product: %s removed from cart: %d", product, cart_id)
        # Republish product in the list of the chosen producer
        for i in list(self.removed_products):
            if self.removed_products[i] == product:
                self.publish(i, product)

    def place_order(self, cart_id):
        """
        Return a list with all the products in the cart.

        :type cart_id: Int
        :param cart_id: id cart
        """
        # Get a copy of the cart list
        with self.locks[CART_LOCK]:
            cart_copy = self.cart_list[cart_id][:]

            # Reset the cart list and its size
            self.cart_list[cart_id] = []
            self.cart_list_sizes[cart_id] = 0

        # Return the cart copy
        self.logger.info("order placed successfully")
        return cart_copy
