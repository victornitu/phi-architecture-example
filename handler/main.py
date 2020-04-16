import os
import time
from abc import ABC, abstractmethod
from json import loads
from kafka import KafkaConsumer
from kafka.consumer.fetcher import ConsumerRecord
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from typing import Dict, Any, Type

EVENT_STORE = os.environ.get('EVENT_STORE', 'localhost:9092')
TOPIC = os.environ.get('TOPIC', 'events')
ENCODING = os.environ.get('ENCODING', 'utf-8')

ENTITY_STORE = os.environ.get('ENTITY_STORE', 'localhost:27017')
DATABASE = os.environ.get('DATABASE', 'entities')


class Handler:
    def __init__(self):
        self.consumer = None

    def start(self) -> None:
        self.connect_consumer()
        for event_record in self.consumer:
            selector = HandlerSelector(event_record)
            print('Product handler processes event of type:', selector.type)
            product_handler = selector.select_product_handler()
            product_handler.process_event()
            print('Customer handler processes event of type:', selector.type)
            customer_handler = selector.select_customer_handler()
            customer_handler.process_event()

    def connect_consumer(self) -> None:
        try:
            self.consumer = KafkaConsumer(TOPIC,
                                          bootstrap_servers=[EVENT_STORE],
                                          value_deserializer=lambda x: loads(x.decode(ENCODING)))
            print('Consumer connected to Event Store')
        except Exception as e:
            print('Failed to connect to Event Store:', e)
            print('Waiting 10 seconds for next attempt')
            time.sleep(10)
            self.connect_consumer()


class HandlerSelector:
    def __init__(self, record: ConsumerRecord):
        self.name = record.value.get('name')
        self.version = record.value.get('version')
        self.payload = record.value.get('payload', {})
        self.type = f'{self.name}:{self.version}'

    def select_product_handler(self) -> 'EventHandler':
        return self.select_handler({
            'product_watched:v1.0': ProductWatched,
            'product_bought:v1.0': ProductBought
        })

    def select_customer_handler(self) -> 'EventHandler':
        return self.select_handler({
            'product_bought:v1.0': CustomerBought
        })

    def select_handler(self, handlers: Dict[str, Type['EventHandler']]) -> 'EventHandler':
        handler = handlers.get(self.type, Unknown)
        return handler(self.name, self.version, self.payload)


class EventHandler(ABC):
    collection_name: str

    @abstractmethod
    def __init__(self, name: str, version: str, payload: Dict[str, Any]):
        self.name = name
        self.version = version
        self.payload = payload
        self.collection = None

    @abstractmethod
    def process_event(self) -> None:
        self.connect_client()

    def connect_client(self) -> None:
        try:
            client = MongoClient(ENTITY_STORE)
            self.collection = client[DATABASE][self.collection_name]
            print('Client connected to Entity Store collection', self.collection_name)
        except ConnectionFailure as e:
            print('Failed to connect to Entity Store:', e)
            print('Waiting 10 seconds for next attempt')
            time.sleep(10)
            self.connect_client()


class ProductWatched(EventHandler):
    collection_name = 'products'

    def __init__(self, name: str, version: str, payload: Dict[str, Any]):
        super().__init__(name, version, payload)
        self.product = self.payload.get('product')
        self.visitor = self.payload.get('visitor')

    def process_event(self) -> None:
        super().process_event()
        self.collection.find_one_and_update(
            filter={'name': self.product},
            update={
                '$inc': {'watched': 1},
            },
            upsert=True
        )
        print(f'Product "{self.product}" was watched by Visitor "{self.visitor}"')


class ProductBought(EventHandler):
    collection_name = 'products'

    def __init__(self, name: str, version: str, payload: Dict[str, Any]):
        super().__init__(name, version, payload)
        self.product = self.payload.get('product')
        self.customer = self.payload.get('customer')

    def process_event(self) -> None:
        super().process_event()
        self.collection.find_one_and_update(
            filter={'name': self.product},
            update={
                '$inc': {'bought': 1}
            },
            upsert=True
        )
        print(f'Product "{self.product}" was bought by Customer "{self.customer}"')


class CustomerBought(EventHandler):
    collection_name = 'customers'

    def __init__(self, name: str, version: str, payload: Dict[str, Any]):
        super().__init__(name, version, payload)
        self.product = self.payload.get('product')
        self.customer = self.payload.get('customer')

    def process_event(self) -> None:
        super().process_event()
        self.collection.find_one_and_update(
            filter={'name': self.customer},
            update={
                '$inc': {
                    'products': 1,
                    self.product: 1
                }
            },
            upsert=True
        )
        print(f'Customer "{self.customer}" bought Product "{self.product}"')


class Unknown(EventHandler):
    def __init__(self, name: str, version: str, payload: Dict[str, Any]):
        super().__init__(name, version, payload)

    def process_event(self) -> None:
        print(f'Unknown event "{self.name}" of version "{self.version}" was ignored')


if __name__ == '__main__':
    main_handler = Handler()
    main_handler.start()
