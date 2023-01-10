#  Starlette & Docker

Remembering how to create a simple starlette app and load it up in docker 

## Running the app

```
cd app
uvicorn run:app --reload
```

### Using docker 

First build the Image and then run

```
docker run -d --name <container_name> -p 80:80 <image>
```