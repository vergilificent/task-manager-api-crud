from fastapi import FastAPI, HTTPException, status, Path, Depends
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datebase import SessionLocal, UserDB, TaskDB
from auth import hash_password, verify_password, create_access_token
from datetime import timedelta
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from auth import SECRET_KEY, ALGORITHM

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#oath2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

#dependency to get current user from token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code = 401, detail = "invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail = "invalid token")
    
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if user is None:
        raise HTTPException(status_code = 401, detail = "user not found")
    return user

#makes fastapi instance
app = FastAPI()

#pydantic models for requests/responses

class UserCreate(BaseModel):
    username: str
    email:str
    password:str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TaskCreate(BaseModel):
    title: str
    description: str

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool

    class Config:
        from_attributes = True

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

#root
@app.get("/")
def root():
    return {"message":"/docs to begin"}

#sign up
@app.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    #check if username already exists
    existing_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code = 400, detail = "username already exists")
    
    #create new user with hashed password
    new_user = UserDB (
        username = user.username,
        email = user.email,
        hashed_password = hash_password(user.password)
    ) 
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message":"user created", "username": user.username}

#log in
@app.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    #find user in datebase.py
    db_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code= 401, detail="invalid credentials")
    #verify password
    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="invalid credentials")
    #create token
    access_token = create_access_token(
        data={"sub": db_user.username},
        expires_delta=timedelta(minutes=30)
    )

    return {"access_token": access_token, "token_type":"bearer"}


#update profile
@app.post("/tasks/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task:TaskCreate, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    new_task = TaskDB(
        title=task.title,
        description=task.description,
        user_id=current_user.id
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

#get all tasks
@app.get("/tasks/")
def get_tasks(db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    tasks = db.query(TaskDB).filter(TaskDB.user_id == current_user.id).all()
    return tasks

#get one task
@app.get("/tasks/{task_id}")
def get_task(task_id= id, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    task = db.query(TaskDB).filter(TaskDB.id == task_id, TaskDB.user_id == current_user.id).first()
    if not task: 
        raise HTTPException(status_code=404, detail="task not found")
    return task

#update task
@app.put("/tasks/{task_id}")
def update_task(task_id: int, tasks: TaskUpdate, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    task = db.query(TaskDB).filter(TaskDB.id == task_id, TaskDB.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    if tasks.title is not None:
        task.title = tasks.title
    if tasks.description is not None:
        task.description = tasks.description
    if tasks.completed is not None:
        task.completed = tasks.completed
    db.commit()
    db.refresh(task)
    return {"message":"task updated", "task":task}

#delete task
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    task = db.query(TaskDB).filter(TaskDB.id == task_id, TaskDB.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    db.delete(task)
    db.commit()

    return {"message":"task deleted", "task":task_id}