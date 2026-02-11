# Task Manager with basic CRUD functions

_Made in FastAPI, using SQLite for the database model._

## Features
- Create tasks
- Delete tasks
- Update tasks
- View all or one specific task
- Create account
- Authentication

## Installation
```bash
pip install -r requirements.txt
```

## Run
```bash
uvicorn tm:app --reload
```

## To authenticate, for authorized users only
1. Log in or sign up.
2. Click the Authorize button on top of /docs.
3. Paste your token in the box.

## Endpoints
- GET `/` - Root, welcome message.
- GET `/tasks/` - View all tasks.
- GET `/tasks/{task_id}` - View specific task.
- POST `/signup` - Create a user.
- POST `/login` - Use existing user.
- PUT `/tasks/{task_id}` - Update task if user is authenticated to do so.
- DELETE `/tasks/{task_id}` - Delete task if user is authenticated to do so.



[project link, ignore](https://github.com/vergilificent/task-manager-api-crud)