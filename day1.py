from flask import Flask, request, url_for
from markupsafe import escape

 
"""
- The instance of the Flask class will create our WSGI app
- Any configuration and URLs will be registred within this class
- We provided the application's module or package name, used to let flaks knows where to look for
resources (static file, templates...)
- The decorator route is used bind the app's URL to the function it want to trigger
- The function default content type to return when using the route decorator is HTML
and it will be rendered to the user's browser
""" 
app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello World</p>"

@app.route("/home")
def home():
    return "<p>Home Page</p>"

"""
- Any user-provided values rendered in the output must be escaped to protect from injection attacks
- HTML templates rendered with Jinja will automatically esacpe the user-provided values
"""

@app.route("/hello")
def hello():
    name = request.args.get("name", "Flask")
    return f"Hello, {escape(name)}"

"""
- Adding variables sections to the URL is possible by marking sections with <variable_name>
- The function then receives the <variable_name> as a keyword argument
- You can use a converter to specify the type of the argument like <converter:variable_name>
- converter types: string, int, float, path, uuid
"""

@app.route("/hello/<string:name>")
def hello_name(name):
    return f"Hello {escape(name)}"

"""
- If the canonical URL for an endpoint has a trailing slash, it is similar to a folder in a file system,
Accessing it without the trailing slash makes Flask redirect the request to canonical URL
- If the canonicla URL for an endpoint has not a trailing slash, it is similar to the pathname of a file,
accessing it with the trailing slash produce "404 error"
"""

@app.route("/path/")
def path():
    return "Path Page"

@app.route("/about")
def about():
    return "about Page"

"""
- By default the route method only accepts the GET requests when accessing the URL
- Merge the common HTTP methods in they share common data
- Creating seperate views based on the request method is also possible
- If GET is present, Flask automatically adds support for the HEAD method and
handles HEAD requests according to the HTTP RFC
- Likewise, OPTIONS is automatically implemented for you
"""

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return "Trying to login in"
    else:
        return "Fill the login from"
    
@app.get("/login2")
def login2_get():
    return "Fill the login form"

@app.post("/login2")
def login2_post():
    return "Trying to login in"

"""
- Dynamic web apps also need static files (CSS & JS files)
- Web server is configured to serve them for you
- Just create a folder called static in your package or next
to your module and it will be available at /static on the application
- To generate URLs for static files, use the special 'static' endpoint name
"""

url_for("static", filename="style.css")

"""
- When Sending a get request to the server
another request is sent to the URL **/favicon.ico**?
"""

"""
- To start the server use: flask --app file_name run
- Shorcuts does exists for that

- Making the server publicly available is done by adding the
--host=0.0.0.0 to the command line when trying to run the server

- Enabling debug mode will let the server reloads if the code change
while providing an interactive debugger in the browser, but comes
with a major risk of allowing execution of arbitrary Python code from
the browser

- The debugger is protected by a pin, but still represents a major security risk
"""