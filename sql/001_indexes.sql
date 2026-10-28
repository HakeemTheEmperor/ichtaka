-- For databases created before these indexes were added to the models
-- (Base.metadata.create_all does not alter existing tables).
CREATE INDEX IF NOT EXISTS ix_posts_created_at ON posts (created_at);
CREATE INDEX IF NOT EXISTS ix_posts_user_id ON posts (user_id);
CREATE INDEX IF NOT EXISTS ix_post_comments_post_id ON post_comments (post_id);
CREATE INDEX IF NOT EXISTS ix_post_comments_parent_id ON post_comments (parent_id);
CREATE INDEX IF NOT EXISTS ix_notifications_recipient_created ON notifications (recipient_id, created_at);
