from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="Advertisement Service", description="API for buy/sell advertisements")

class AdvertisementBase(BaseModel):
    title: str
    description: str
    price: float
    author: str

class AdvertisementCreate(AdvertisementBase):
    pass

class AdvertisementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    author: Optional[str] = None

class Advertisement(AdvertisementBase):
    id: int
    created_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# In-memory storage for advertisements
advertisements_db = {}
next_id = 1

@app.post("/advertisement", response_model=Advertisement, status_code=201)
async def create_advertisement(advertisement: AdvertisementCreate):
    """
    Create a new advertisement
    """
    global next_id
    advertisement_id = next_id
    next_id += 1
    
    new_advertisement = Advertisement(
        id=advertisement_id,
        title=advertisement.title,
        description=advertisement.description,
        price=advertisement.price,
        author=advertisement.author,
        created_at=datetime.now()
    )
    advertisements_db[advertisement_id] = new_advertisement
    return new_advertisement

@app.get("/advertisement/{advertisement_id}", response_model=Advertisement)
async def get_advertisement(advertisement_id: int):
    """
    Get advertisement by ID
    """
    if advertisement_id not in advertisements_db:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    return advertisements_db[advertisement_id]

@app.patch("/advertisement/{advertisement_id}", response_model=Advertisement)
async def update_advertisement(advertisement_id: int, advertisement_update: AdvertisementUpdate):
    """
    Update advertisement by ID
    """
    if advertisement_id not in advertisements_db:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    
    stored_advertisement = advertisements_db[advertisement_id]
    
    update_data = advertisement_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stored_advertisement, field, value)
    
    advertisements_db[advertisement_id] = stored_advertisement
    return stored_advertisement

@app.delete("/advertisement/{advertisement_id}", status_code=204)
async def delete_advertisement(advertisement_id: int):
    """
    Delete advertisement by ID
    """
    if advertisement_id not in advertisements_db:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    del advertisements_db[advertisement_id]
    return None

@app.get("/advertisement", response_model=List[Advertisement])
async def search_advertisements(
    title: Optional[str] = Query(None, description="Filter by title"),
    description: Optional[str] = Query(None, description="Filter by description"),
    author: Optional[str] = Query(None, description="Filter by author"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    created_after: Optional[datetime] = Query(None, description="Filter advertisements created after this date"),
    created_before: Optional[datetime] = Query(None, description="Filter advertisements created before this date")
):
    """
    Search advertisements by various fields
    """
    filtered_advertisements = []
    
    for advertisement in advertisements_db.values():
        # Filter by title (case-insensitive partial match)
        if title and title.lower() not in advertisement.title.lower():
            continue
        
        # Filter by description (case-insensitive partial match)
        if description and description.lower() not in advertisement.description.lower():
            continue
        
        # Filter by author (case-insensitive partial match)
        if author and author.lower() not in advertisement.author.lower():
            continue
        
        # Filter by minimum price
        if min_price is not None and advertisement.price < min_price:
            continue
        
        # Filter by maximum price
        if max_price is not None and advertisement.price > max_price:
            continue
        
        # Filter by creation date range
        if created_after and advertisement.created_at < created_after:
            continue
            
        if created_before and advertisement.created_at > created_before:
            continue
        
        filtered_advertisements.append(advertisement)
    
    return filtered_advertisements

@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {"message": "Advertisement Service API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
