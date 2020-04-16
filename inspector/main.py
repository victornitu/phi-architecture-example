import os
from pymongo import MongoClient
from pymongo.collection import Collection
from sanic import Sanic
from sanic.exceptions import NotFound, ServerError
from sanic.request import Request
from sanic.response import json, HTTPResponse

ENTITY_STORE = os.environ.get('ENTITY_STORE', 'localhost:27017')
DATABASE = os.environ.get('DATABASE', 'entities')

app = Sanic(name='Inspector')


@app.route('/v1.0/product')
async def inspect_products(request: Request) -> HTTPResponse:
    collection = connect_collection('products')
    products = []
    for product in collection.find():
        product.pop('_id')
        products.append(product)
    return json({'products': products})


@app.route('/v1.0/customer')
async def inspect_customers(request: Request) -> HTTPResponse:
    collection = connect_collection('customers')
    customers = []
    for customer in collection.find():
        customer.pop('_id')
        customers.append(customer)
    return json({'customers': customers})


def connect_collection(name: str) -> Collection:
    client = MongoClient(ENTITY_STORE)
    return client[DATABASE][name]


@app.exception(NotFound)
async def handle_not_found(request, e):
    error = f'{request.url} not found: {e}'
    print(error)
    return json({'message': error}, status=404)


@app.exception(ServerError)
async def handle_server_error(_, e):
    error = f'Server error: {e}'
    print(error)
    return json({'message': error}, status=500)


@app.exception(Exception)
async def handle_exception(_, e):
    error = f'Unexpected error: {e}'
    print(error)
    return json({'message': error}, status=500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
