from typing import List
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()


class Client(BaseModel):
    client_id: int
    age: int


def client_age(client_id: int) -> int:
    return client_id % 100


@app.get("/client/{client_id}", response_model=Client)
def get_client(client_id: int) -> Client:
    return Client(client_id=client_id, age=client_age(client_id))


class MultiIdRequest(BaseModel):
    client_ids: List[int]


class MultipleClients(BaseModel):
    clients: List[Client]


@app.post("/clients/", response_model=MultipleClients)
def post_client(request: MultiIdRequest) -> MultipleClients:
    return MultipleClients(
        clients=[
            Client(client_id=client_id, age=client_age(client_id))
            for client_id in request.client_ids
        ]
    )
