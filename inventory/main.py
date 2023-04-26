from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from redis_om import get_redis_connection, HashModel
import os

app = FastAPI()
load_dotenv()


redis = get_redis_connection(
    host=os.getenv("HOST"),
    port=os.getenv("PORT"),
    password=os.getenv("PASSWORD"),
    decode_responses=True
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'], # front end(react),
    allow_methods=['*'], # all methods
    allow_headers=['*']
)


class Product(HashModel):
    name: str
    price: float
    quantity: int

    class Meta: # 엔티티 클래스와 db 연결
        database = redis


@app.get("/products")
def all():
    return [format(pk) for pk in Product.all_pks()]


def format(pk: str):
    product = Product.get(pk)
    return {
        'id': product.pk,
        'name': product.name,
        'price': product.price,
        'quantity': product.quantity
    }


@app.post("/products")
def create(product: Product):
    return product.save()


@app.get("/products/{pk}")
def get(pk: str):
    return Product.get(pk)


@app.delete("/products/{pk}")
def get(pk: str):
    return Product.delete(pk)


@app.get("/")
async def root():
    return {"message": "Hello World", "host": os.getenv("HOST")}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

