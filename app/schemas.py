from pydantic import BaseModel, EmailStr

from datetime import datetime


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class CategoryCreate(BaseModel):
    name: str


class CategoryUpdate(BaseModel):
    name: str
    
    
    
class TransactionCreate(BaseModel):
    category_id: int
    amount: int
    type: str
    description: str| None = None
    date: datetime
    

class TransactionUpdate(BaseModel):
    category_id: int
    amount: float
    type: str
    description: str| None = None
    date: datetime