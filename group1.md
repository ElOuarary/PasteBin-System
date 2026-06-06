Group 1 — Basic API
What you are building: The Pastebin doesn't exist yet. This group creates the HTTP surface — a stateless FastAPI service that accepts raw text and returns a generated paste ID. Nothing is stored. The request comes in, a unique ID is generated, and it goes back out. This sounds trivial but it establishes the shape of everything that follows: how requests are validated, how errors are returned, how the API communicates its contract. If this layer handles malformed input badly, every future group inherits that rot.
Constraints you must meet:

All endpoints return correct HTTP status codes
Response time under 20ms for any input on localhost
No unhandled exceptions reachable by malformed input

Measurement method: Run curl or HTTPie against every endpoint. All return correct status codes and response shapes for valid and invalid input.
Implementation levels:

Intern: One POST /pastes endpoint. Accepts a JSON body with a content field. Generates a UUID. Returns {"id": "<uuid>"}. No validation. No error handling beyond what FastAPI gives you for free.
Junior: Add input validation — content must not be empty, must not exceed 10MB. Return 422 with a readable message for bad input. Add a GET /pastes/{id} that always returns 404 with {"error": "not found"} (no storage yet — this is the stub that Group 2 will fill). Add a GET /health endpoint returning {"status": "ok"}.
Senior: Every possible malformed request — missing body, wrong content-type, null content, content over the limit, non-string content — returns the correct status code and a consistent error shape {"error": "<message>"}. Response time verified under 20ms with curl -w "%{time_total}". No unhandled 500s reachable from any input.

Prerequisite: None.
Vocabulary to know before starting:

Stateless: The server holds no state between requests. Every request carries all the information needed to process it. This is what makes the system horizontally scalable later.
HTTP status codes: 200 OK, 201 Created, 400 Bad Request, 404 Not Found, 422 Unprocessable Entity, 500 Internal Server Error. Use them precisely — 422 is for validation failures, 400 is for malformed requests.
Request/response cycle: Client sends a request (method + path + headers + body), server processes it, returns a response (status + headers + body). FastAPI abstracts this but you need to know what's underneath.
Idempotency: GET requests must be idempotent — calling them multiple times produces the same result. POST is not idempotent — each call creates something new.
Content-Type: The Content-Type: application/json header tells the server how to parse the body. FastAPI enforces this automatically; understand why it matters.

Valid improvements for this group: Robust error handling, input validation rules (min/max length, allowed characters), multiple HTTP methods on the same endpoint, encoding options for paste content. Do not add storage, auth, external calls, or caching.