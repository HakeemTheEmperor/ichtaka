-- Lets ILIKE '%text%' search use an index instead of scanning every row.
-- For databases created before these indexes were added to the models.
-- On a large table, use CREATE INDEX CONCURRENTLY (outside a transaction) to avoid blocking writes.
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS ix_posts_title_trgm ON posts USING gin (title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS ix_posts_description_trgm ON posts USING gin (description gin_trgm_ops);
CREATE INDEX IF NOT EXISTS ix_user_account_pseudonym_trgm ON user_account USING gin (pseudonym gin_trgm_ops);
