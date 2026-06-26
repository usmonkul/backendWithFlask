# Flask Backend API

Simple Flask backend API with MySQL, deployed on cPanel.

## Tech Stack

- **Runtime**: Python
- **Framework**: Flask
- **Database**: MySQL
- **Authentication**: Custom session-based (UUID tokens)
- **Password Hashing**: bcrypt
- **Deployment**: cPanel

## Setup Instructions

### 1. Database Setup (via phpMyAdmin)

Create the database and tables manually in phpMyAdmin:

**users table:**
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**sessions table:**
```sql
CREATE TABLE sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 2. Environment Variables

Set these in your cPanel environment:

- `DB_HOST` - MySQL host (usually `localhost` for cPanel)
- `DB_PORT` - MySQL port (usually `3306`)
- `DB_NAME` - Database name
- `DB_USER` - MySQL username
- `DB_PASSWORD` - MySQL password
- `ADMIN_API_KEY` - Secret key for admin endpoints
- `CORS_ORIGINS` - (Optional) Comma-separated list of allowed origins (default: `*` allows all)
  - Example: `https://example.com,https://www.example.com`
  - Use `*` to allow all origins (less secure)

**Note:** `PORT` is NOT needed in cPanel - cPanel handles the port automatically. The PORT variable in the code is only used for local development.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

## API Endpoints

### Authentication (`/auth`)

- `POST /auth/login` - Login user (returns token)
  ```json
  {
    "username": "user123",
    "password": "password123"
  }
  ```

- `POST /auth/logout` - Logout user (requires Bearer token)
  ```
  Authorization: Bearer <token>
  ```

- `GET /auth/me` - Get current user info (requires Bearer token)
  ```
  Authorization: Bearer <token>
  ```

### Admin (`/admin`) - Requires `x-admin-token` header

- `POST /admin/users` - Create user
  ```
  x-admin-token: <admin-api-key>
  ```
  ```json
  {
    "username": "newuser",
    "password": "password123",
    "is_admin": false
  }
  ```

- `GET /admin/users` - List all users
  ```
  x-admin-token: <admin-api-key>
  ```

- `DELETE /admin/users/:id` - Delete user (non-admin only)
  ```
  x-admin-token: <admin-api-key>
  ```

- `PATCH /admin/users/:id/password` - Update user password
  ```
  x-admin-token: <admin-api-key>
  ```
  ```json
  {
    "password": "newpassword123"
  }
  ```

### Health

- `GET /health` - Health check (returns `{"status":"ok"}`)
- `GET /` - Root endpoint (returns API info)

## Security Features

- **Rate Limiting**: 
  - Login endpoint: 5 requests per minute
  - Create user endpoint: 10 requests per minute
  - Default limits: 200 requests per day, 50 per hour for all endpoints
- **CORS**: Configurable via `CORS_ORIGINS` environment variable (default: allows all origins)
- **Password Hashing**: bcrypt with salt
- **Session Management**: Tokens expire after 7 days
- **SQL Injection Protection**: Parameterized queries
- **Admin Protection**: Separate API key required for admin endpoints

## Notes

- Database and tables are created manually via phpMyAdmin (NOT by code)
- Session tokens expire after 7 days
- Admin users cannot be deleted

