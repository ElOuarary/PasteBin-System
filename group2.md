Group 2 — Data Persistence
What you are building: Pastes currently live in a dict that dies with the process. This group replaces that with a real database and expands the data model to reflect what a Pastebin actually needs to store: who created a paste, when it expires, how many times it's been viewed, and what tags categorize it. Without this, every server restart wipes all content, relationships between entities can't be enforced, and the system has no foundation for the auth layer coming in Group 3.
Constraints you must meet:

All CRUD operations complete under 100ms on localhost with up to 10,000 rows
Foreign key constraints enforced at the database level
No data loss on server restart

Measurement method: Run CRUD operations via Postman or a test script. Verify data persists across server restarts. Verify relationships are enforced at the database level.
Implementation levels:

Intern: Replace memory = {} with SQLite + SQLAlchemy. One table: pastes with id, content, created_at. CRUD still works, data survives restart. Nothing else.
Junior: Full data model. Tables: pastes (id, content, created_at, expires_at, view_count, is_private), users (id, username, email, created_at), tags (id, name), paste_tags (paste_id, tag_id). Foreign keys enforced at DB level. GET /pastes supports filtering by tag. View count increments on every read. Expired pastes return 410 Gone.
Senior: Switch from SQLite to PostgreSQL (run it in Docker). Add indexes on expires_at and created_at for the queries you know are coming. Basic search endpoint GET /pastes?search=keyword that queries content. Verify all CRUD under 100ms at 10,000 rows — populate the DB with a seed script and measure with your test script capturing time_total. Expired paste cleanup is a manual endpoint for now (DELETE /pastes/expired) — the scheduled job comes in Group 5.

Prerequisite: None.
Vocabulary to know before starting:

ORM (Object-Relational Mapper): Maps Python classes to database tables. SQLAlchemy is the standard. You define a Base model, declare columns with types, and the ORM generates SQL. You don't write raw SQL for basic operations, but you need to know what SQL it generates.
Foreign key constraint: A database-level rule that a value in column A must exist in column B of another table. If you only enforce this in Python, a direct DB write bypasses it. Enforce it in the schema.
Migration: A versioned, repeatable change to the database schema. Alembic is the tool for SQLAlchemy. Without migrations, schema changes require dropping and recreating tables — which destroys data.
Index: A data structure that speeds up lookups on a column at the cost of slower writes and extra storage. Add them on columns you filter or sort by frequently. Missing indexes on a 10,000-row table is where the 100ms constraint will kill you.
Connection pooling: SQLAlchemy maintains a pool of open DB connections rather than opening a new one per request. Understand the SessionLocal pattern — one session per request, closed after the response.

Valid improvements for this group: Richer data models (custom short codes instead of UUIDs, burn-after-read pastes, syntax highlighting language field), pagination on list endpoints, full-text search, more filtering options (by date range, by user), soft deletes. Do not add auth, caching, rate limiting, or async queues.