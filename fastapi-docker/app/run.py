from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()


class Client(BaseModel):
    client_id: int
    age: int


def determanistic_age_from_client_id(client_id: int) -> int:
    return client_id % 100


@app.get("/client/{client_id}", response_model=Client)
def get_client(client_id: int) -> Client:
    return Client(client_id=client_id, age=determanistic_age_from_client_id(client_id))


@app.post("/client/", response_model=Client)
def post_client(client_id: int) -> Client:
    return Client(client_id=client_id, age=determanistic_age_from_client_id(client_id))
