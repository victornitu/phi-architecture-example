import os
from json import dumps
from kafka import KafkaProducer
from sanic import Sanic
from sanic.exceptions import NotFound, ServerError
from sanic.request import Request
from sanic.response import json, HTTPResponse

EVENT_STORE = os.environ.get('EVENT_STORE', 'localhost:9092')
TOPIC = os.environ.get('TOPIC', 'events')
ENCODING = os.environ.get('ENCODING', 'utf-8')

app = Sanic(name='Publisher')


@app.route('/v1.0/product/<product_name:[A-z0-9]+>/watched', methods=['POST'])
async def visitor_watched_product(request: Request, product_name: str) -> HTTPResponse:
    producer = connect_producer()
    event = {
        'name': 'product_watched',
        'version': 'v1.0',
        'payload': {
            'product': product_name,
            'visitor': request.json.get('visitor', 'anonymous')
        }
    }
    producer.send(TOPIC, event)
    return json({'event': event})


@app.route('/v1.0/customer/<customer_name:[A-z]+>/bought', methods=['POST'])
async def customer_bought_products(request: Request, customer_name: str) -> HTTPResponse:
    producer = connect_producer()
    events = []
    for product_name in request.json.get('products', []):
        events.append({
            'name': 'product_bought',
            'version': 'v1.0',
            'payload': {
                'product': product_name,
                'customer': customer_name
            }
        })
    [producer.send(TOPIC, event) for event in events]
    return json({'events': events})


def connect_producer() -> KafkaProducer:
    return KafkaProducer(bootstrap_servers=[EVENT_STORE],
                         value_serializer=lambda x: dumps(x).encode(ENCODING))


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
