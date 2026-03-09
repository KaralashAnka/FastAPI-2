from fastapi import FastAPI, HTTPException, Query, Depends, status
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta

from database import get_db, Advertisement as AdvertisementModel, User as UserModel
from schemas import (
    AdvertisementCreate, AdvertisementUpdate, AdvertisementResponse,
    UserCreate, UserUpdate, UserResponse, Token, LoginRequest
)
from auth import (
    get_password_hash, verify_password, create_access_token, 
    get_current_user, ACCESS_TOKEN_EXPIRE_HOURS
)

app = FastAPI(title="Advertisement Service", description="API for buy/sell advertisements")

# --- Auth Routes ---

@app.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- User Routes ---

@app.post("/user", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate, 
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user)
):
    # Check if someone is trying to create an admin
    if user.role == "admin":
        if not current_user or current_user.role != "admin":
            raise HTTPException(
                status_code=403, 
                detail="Only admins can create other admin users"
            )

    db_user = db.query(UserModel).filter(UserModel.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = UserModel(
        username=user.username,
        password=hashed_password,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/user", response_model=List[UserResponse])
async def get_users(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return db.query(UserModel).all()

@app.get("/user/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.patch("/user/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check permissions: admin or self
    if current_user.role != "admin" and current_user.id != user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"])
    
    # Only admin can change roles
    if "role" in update_data and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can change roles")

    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user

@app.delete("/user/{user_id}", status_code=204)
async def delete_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check permissions: admin or self
    if current_user.role != "admin" and current_user.id != user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(user)
    db.commit()
    return None

# --- Advertisement Routes ---

@app.post("/advertisement", response_model=AdvertisementResponse, status_code=201)
async def create_advertisement(
    advertisement: AdvertisementCreate, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    db_advertisement = AdvertisementModel(
        **advertisement.model_dump(),
        owner_id=current_user.id
    )
    db.add(db_advertisement)
    db.commit()
    db.refresh(db_advertisement)
    
    # Add owner_name for response
    if db_advertisement.owner:
        db_advertisement.owner_name = db_advertisement.owner.username
    else:
        db_advertisement.owner_name = current_user.username
    return db_advertisement

@app.get("/advertisement/{advertisement_id}", response_model=AdvertisementResponse)
async def get_advertisement(
    advertisement_id: int, 
    db: Session = Depends(get_db)
):
    advertisement = db.query(AdvertisementModel).filter(
        AdvertisementModel.id == advertisement_id
    ).first()
    
    if not advertisement:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    
    # Add owner_name for response
    if advertisement.owner:
        advertisement.owner_name = advertisement.owner.username
    
    return advertisement

@app.patch("/advertisement/{advertisement_id}", response_model=AdvertisementResponse)
async def update_advertisement(
    advertisement_id: int, 
    advertisement_update: AdvertisementUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    advertisement = db.query(AdvertisementModel).filter(
        AdvertisementModel.id == advertisement_id
    ).first()
    
    if not advertisement:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    
    # Check permissions: admin or owner
    if current_user.role != "admin" and advertisement.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    update_data = advertisement_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(advertisement, field, value)
    
    db.commit()
    db.refresh(advertisement)
    
    # Add owner_name for response
    if advertisement.owner:
        advertisement.owner_name = advertisement.owner.username
    
    return advertisement

@app.delete("/advertisement/{advertisement_id}", status_code=204)
async def delete_advertisement(
    advertisement_id: int, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    advertisement = db.query(AdvertisementModel).filter(
        AdvertisementModel.id == advertisement_id
    ).first()
    
    if not advertisement:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    
    # Check permissions: admin or owner
    if current_user.role != "admin" and advertisement.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(advertisement)
    db.commit()
    return None

@app.get("/advertisement", response_model=List[AdvertisementResponse])
async def search_advertisements(
    title: Optional[str] = Query(None, description="Filter by title"),
    description: Optional[str] = Query(None, description="Filter by description"),
    owner_id: Optional[int] = Query(None, description="Filter by owner ID"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    created_after: Optional[datetime] = Query(None, description="Filter advertisements created after this date"),
    created_before: Optional[datetime] = Query(None, description="Filter advertisements created before this date"),
    db: Session = Depends(get_db)
):
    query = db.query(AdvertisementModel)
    
    if title:
        query = query.filter(AdvertisementModel.title.ilike(f"%{title}%"))
    if description:
        query = query.filter(AdvertisementModel.description.ilike(f"%{description}%"))
    if owner_id:
        query = query.filter(AdvertisementModel.owner_id == owner_id)
    if min_price is not None:
        query = query.filter(AdvertisementModel.price >= min_price)
    if max_price is not None:
        query = query.filter(AdvertisementModel.price <= max_price)
    if created_after:
        query = query.filter(AdvertisementModel.created_at >= created_after)
    if created_before:
        query = query.filter(AdvertisementModel.created_at <= created_before)
    
    results = query.all()
    # Add owner_name for response
    for adv in results:
        if adv.owner:
            adv.owner_name = adv.owner.username
    
    return results

@app.get("/")
async def root():
    """
    Root endpoint with API documentation
    """
    return {
        "message": "Advertisement Service API",
        "version": "1.0.0",
        "description": "API for creating and managing buy/sell advertisements",
        "endpoints": {
            "POST /advertisement": "Create new advertisement",
            "GET /advertisement/{id}": "Get advertisement by ID",
            "PATCH /advertisement/{id}": "Update advertisement by ID", 
            "DELETE /advertisement/{id}": "Delete advertisement by ID",
            "GET /advertisement": "Search advertisements with filters",
            "GET /docs": "Interactive API documentation (Swagger)",
            "GET /redoc": "API documentation (ReDoc)"
        },
        "search_filters": {
            "title": "Filter by title (partial match)",
            "description": "Filter by description (partial match)",
            "author": "Filter by author (partial match)",
            "min_price": "Minimum price filter",
            "max_price": "Maximum price filter",
            "created_after": "Filter advertisements created after this date (ISO format)",
            "created_before": "Filter advertisements created before this date (ISO format)"
        },
        "examples": {
            "create_advertisement": {
                "method": "POST",
                "url": "/advertisement",
                "body": {
                    "title": "iPhone 15 Pro",
                    "description": "New iPhone 15 Pro, excellent condition",
                    "price": 999.99,
                    "author": "John Doe"
                }
            },
            "search_by_description": {
                "method": "GET", 
                "url": "/advertisement?description=iphone&min_price=500&max_price=1500"
            },
            "get_by_id": {
                "method": "GET",
                "url": "/advertisement/1"
            },
            "update_advertisement": {
                "method": "PATCH",
                "url": "/advertisement/1", 
                "body": {
                    "price": 899.99
                }
            }
        },
        "database": "SQLite with SQLAlchemy ORM",
        "features": [
            "Integer auto-increment IDs",
            "Full-text search in title, description, author",
            "Price range filtering", 
            "Date range filtering",
            "Pydantic v2 validation",
            "RESTful API design"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
