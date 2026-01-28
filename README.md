# ICHTAKA API 🛡️

**Ichtaka** is a secure, anonymous reporting platform designed to empower individuals to report incidents or share information without fear of retribution.

## Features

- **🔐 True Anonymity**: Uses pseudonyms and secure verification to protect reporter identity.
- **📝 Incident Reporting**: Easy-to-use interface for creating detailed reports.
- **💬 Community Engagement**: Vote and comment on reports to build consensus and provide additional context.
- **🚀 Fast & Scaleable**: Built with FastAPI and PostgreSQL for high performance.

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: [PostgreSQL](https://www.postgresql.org/) with [SQLAlchemy](https://www.sqlalchemy.org/)
- **Environment**: [uv](https://docs.astral.sh/uv/) for lightning-fast Python package management.
- **Security**: Argon2 for password hashing, JWT for token-based authentication.

---

## 🚀 Getting Started

### Prerequisites

- [Python 3.13+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Recommended)
- [Docker](https://www.docker.com/) (Optional, for database)

### Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/HakeemTheEmperor/ichtaka.git
   cd ichtaka-api
   ```

2. **Sync dependencies**:

   ```bash
   uv sync
   ```

3. **Set up Environment Variables**:
   Create a `.env` file in the root directory (refer to `.env.example` if available, otherwise check `src/config.py`).
   ```env
   DATABASE_URL=postgresql://user:password@localhost/dbname
   SECRET_KEY=your_secret_key
   ```

### Running the App

Instead of the long uvicorn command, you can now use the simplified shortcut:

```bash
uv run start
```

_This command runs the server at `http://0.0.0.0:8000` with hot-reload enabled._

---

## 🛤️ API Routes

### Authentication (`/v1/auth`)

- `GET  /check-username`: Check if a pseudonym is already in use.
- `POST /signup`: Create a new anonymous account.
- `POST /login`: Login to the platform.
- `POST /verify`: Dual-factor/Verification step after signup/login.

### Reports (`/v1/reports`)

- `POST /`: Create a new report.
- `GET  /`: Fetch the report feed (with pagination and filtering).
- `POST /{id}/vote`: Cast a vote (up/down) on a report.
- `POST /{id}/comments`: Add a comment to a report.
- `PATCH /{id}/status`: (Admin) Update the status of a report (e.g., Pending, Resolved).

### Posts (`/v1/post`)

- `POST /posts/`: Create a general post.
- `GET  /posts/`: Get list of posts.
- `GET  /posts/{id}`: Get post details.
- `PUT  /posts/{id}`: Update a post.
- `DELETE /posts/{id}`: Delete a post.

---

## 🔌 Real-time Updates (WebSockets)

Ichtaka supports real-time updates via WebSockets. Connect to the following endpoint to receive live event notifications:

- **Endpoint**: `ws://localhost:8000/ws`

### Supported Events

The server broadcasts JSON messages with an `event` type and associated `data`:

| Event           | Description                                |
| :-------------- | :----------------------------------------- |
| `new_post`      | Triggered when a new post is created.      |
| `update_post`   | Triggered when a post is updated.          |
| `delete_post`   | Triggered when a post is deleted.          |
| `new_comment`   | Triggered when a new comment is added.     |
| `vote_update`   | Triggered when a vote count changes.       |
| `status_update` | Triggered when a post's status is changed. |

### Example Message

```json
{
  "event": "new_post",
  "data": {
    "id": 1,
    "title": "Incident at Main St",
    "severity": "High",
    "created_at": "2026-01-28T10:00:00Z"
  }
}
```

---

## 🔄 Project Flow

1. **Identity Creation**: Users sign up with a pseudonym. No real names or emails are stored in the core reporting flow.
2. **Verification**: After signup/login, users verify their identity.
3. **Reporting**: Verified users submit reports.
4. **Engagement**: The community interacts with reports via votes and comments.
5. **Resolution**: Admins can update report statuses as they are investigated and addressed.

---

## 🛠️ Development

- **Database Migrations**: Uses SQLAlchemy `Base.metadata.create_all` on startup.
- **Standards**: Pydantic for data validation and OpenAPI generation.
- **Documentation**: Access the interactive Swagger UI at `http://localhost:8000/docs`.

---

_Ichtaka - Speak your truth, securely._
