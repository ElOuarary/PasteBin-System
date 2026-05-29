from flask import Flask, request, abort, make_response, redirect, render_template, url_for
from werkzeug.utils import secure_filename
app = Flask(__name__)

"""
-> URL Buiding
- Building a specific URL for a function:
-- Use the "url_for" function
-- Any number of keyword arguments, each corresponding to a variable part of the URL rule
-- Unknown variable parts are appended to the URL as query parameters

- Why building the URL instead of hardcoding them:
-- Reversing is often more descriptive than hard-coding the URLs
-- You can change your URLs in one go instead of needing to remember to manually change hard-coded URLs
-- URL building handles escaping of special characters transparently
-- The generated paths are always absolute, avoiding unexpected behavior of relative paths in browsers
-- If your application is placed outside the URL root, for example, in /myapplication instead of /, url_for() properly handles that for you
"""

@app.route("/login1")
def login1():
    return "login"

@app.route("/user/<username>")
def profile(username):
    return f"{username}\'s profile"

with app.test_request_context():
    print(url_for("login"))
    print(url_for("login"), next="/")
    print(url_for("profile", username="Abdelaziz"))

"""
-> Rendering Temaplates
- Flask configure Jinja template engine automatically generate templates and ensure the data escaping for security
- Templates can be used to generate any text file
- To render a template use the render_template with the template to render and the keyword arguments for the variables
to pass in to the engine template
- Flaks will look at the templates in the template folder
- If your application is a module, this folder is next to that module, if it is a package it is actually inside your package

"""

@app.route("/hello")
@app.route("/hello/<name>")
def hello(name=None):
    return render_template("hello.txt", name=name)

"""
- To handle the data sent by the client to the server, use the gloabal object reqeust
- How this object is global and how Flaks manages to be still threadsafe? The answer is context locals
-- 
"""

"""
- The reqeust object and some common operations
-- method attribute: To access the request method
-- form (if a key is not present, it will raises a KeyError if not handled HTTP 400 Bad Request error page is shown instead) attribute:
To access  form data
-- args attribute: To access parameters submitted in the URL (?key=value)
"""

@app.route("/login",  methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        error = "Invalid username/password"
        return f"{request.form["username"]}:{request.form["passowrd"]}"
    name = request.args.get("name", "")
    render_template("/index.html", error)
    
"""
-> Handling uploaded files in flask
- make sure not to forget to set the enctype="multipart/form-data" attribute
on the HTML form, otherwise the browser will not transmit the files at all
- Uploaded files are stored in memory or at a temporary location on the filesystem
- files attribute of the request object is used to access these files
- Each uploaded file is stored in that dictionary
- The file behaves just like a standard Python file object, but it also has a save()
method that allows you to store that file on the filesystem of the server
- To know how the file was named on the client before it was uploaded to your application
you can access the filename attribute
- If you want to use the filename of the client to store the file on the server,
pass it through the secure_filename() function that Werkzeug provides for you
"""

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        f = request.files.get("the_file")
        f.save("./file.txt")
        f.save(f"./file/{secure_filename(f.filename)}")
        
"""
-> Cookies
- To get the cookies use the cookies attribute for the request object
- To send cookies use the set_cookie method for the response objects
"""

@app.route("/")
def index():
    name = request.cookies.get("name", "")
    resp = make_response(render_template(...))
    resp.set_cookie("name", name)
    return resp

"""
-> Redirects and Errors
- To redirect a user to another endpoint, use the redirect() function
- To abort a request early with an error code, use the abort() function
- If you want to customize the error page, you can use the errorhandler() decorator
- The second return value of a decorated function in Flask is refering the status code of
the HTTP request
"""

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login")
def login():
    abort(401)
    # This will never be executed
    return

@app.errorhandler(404)
def page_not_found(error):
    return render_template("page_not_found.html"), 404

"""
-> About Responses
- The return value from a view function is automatically converted into a response object for you
- If a response object of the correct type is returned it is directly returned from the view
- If it is a string, a response object is created with that data and the default parameters
- If it is an iterator or generator returning strings or bytes, it is treated as a streaming response
- If it is a dict or list, a response object is created using jsonify()
- If a tuple is returned the items in the tuple can provide extra information,
such tuples have to be in the form (response, status), (response, headers), or
(response, status, headers). The status value will override the status code and headers can be a list
or dictionary of additional header values
- If none of that works, Flask will assume the return value is a valid WSGI application and convert that into a response objec
"""

@app.errorhandler(404)
def page_not_found(error):
    resp = make_response(render_template(...), 404)
    resp.headers["X-something"] = "A value"
    return resp

"""
-> APIs with JSON
- Flaks support sending bakc json response object, if returning dicts or lists
from a view with the condition of all data must be JSON serializable
- For complex types such as database models, use a serialization library or Flask extension
to convert the data to valid JSON types firs
"""

@app.route("/me")
def me_api():
    return {
        "username": "Abdelaziz",
        "email": "abdelaziz"
    }
    
@app.route("/list")
def list_api():
    return [
        {"name": "abdelaziz"},
        {"name": "elouarary"}
    ]