FastAPI stands on the shoulders of giants:
- Starlette for the web parts
- Pydantic for the data parts

1- FastAPI installed
2- Create the main.py file with the FastAPI app
3- Defined the endpoints with path parameters and query parameters
4- Run the developement server using fastapi dev
5- Use the automatic interactive API docs provided by Swagger UI or ReDoc
6- Extract the body from the request

fastapi dev: reads your main.py file automatically, detects the FastAPI app in it,
and starts with auto-reload enabled developement server using Uvicorn.

Handling HTTP exception using the HTTPException class, the object created by that class
should be raised not returned since it is a python exception
for details about the exception you can pass any value that can be converted to JSON,
check https://fastapi.tiangolo.com/tutorial/handling-errors/#the-resulting-response
for more details

