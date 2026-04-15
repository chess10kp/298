from fastapi import FastAPI
from app.services.ride import RideService
from app.services.authentication import AuthService

app = FastAPI()
ride = RideService()
auth = AuthService()

@app.get("/")
def home():
    return {"message": "Fruger API"}

@app.get("/rides")
def rides():
    return ride.rides()

@app.post("/ride")
def create(pickup: str, drop: str, distance: float):
    return ride.create(pickup, drop, distance)

@app.put("/ride/cancel")
def cancel(ride_id: int):
    return ride.cancel(ride_id)

@app.post("/register")
def register(email: str, password: str):
    return auth.register(email, password)

@app.post("/login")
def login(email: str, password: str):
    return auth.login(email, password)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)
