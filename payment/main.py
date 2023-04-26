import time

from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from redis_om import get_redis_connection, HashModel
from starlette.background import BackgroundTasks
from starlette.requests import Request
import os
import requests

app = FastAPI()
load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'], # front end(react),
    allow_methods=['*'], # all methods
    allow_headers=['*']
)

redis = get_redis_connection(
    host=os.getenv("HOST"),
    port=os.getenv("PORT"),
    password=os.getenv("PASSWORD"),
    decode_responses=True
)

app = FastAPI()


class Order(HashModel):
    product_id: str
    price: float
    fee: float
    total: float
    quantity: int
    status: str  # pending(처리중), completed(처리완료), refunded(오류)

    class Meta:
        database = redis


@app.get('/orders/{pk}')
def get(pk: str):
    return Order.get(pk)


@app.post('/orders')
async def create(request: Request, background_tasks: BackgroundTasks): # id, quantity
    body = await request.json()

    req = requests.get(os.getenv('INVENTORY_DOMAIN')+'/products/%s' % body['id'])
    product = req.json()

    order = Order(
        product_id=product['pk'],
        price=product['price'],
        fee=0.2*product['price'],
        total=1.2*product['price'],
        quantity=body['quantity'],
        status='pending'
    )

    order.save()

    background_tasks.add_task(order_complete, order) # task, argument

    return order


# 목표 : pending 상태의 주문을 바로 저장하고 5초 뒤에 completed로 업데이트해서 db 반영
# 이때 클라이언트는 pending 상태의 주문을 바로 받아서 사용할 수 있다. 5초 뒤에 다시 주문을 조회하면 completed 상태이다.
def order_complete(order: Order):
    time.sleep(5)
    order.status = 'completed'
    order.save()
    # stream produce
    redis.xadd('order_completed', order.dict(), '*') # key, value, generated id


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
