from app.services.database import DBSession

class RideService:
    
    def __init__(self, database="fruger.db"):
        self.db = DBSession(database)

    def rides(self):

        try:

            result = self.db.multiple("SELECT * FROM rides")      # Pull all stored rides for the /rides endpoint

            return result
        
        except Exception as e:

            return {"error": str(e)}

    def create(self, pickup, drop, distance):

        try:

            if not pickup or not drop:

                return {"error": "Pickup and drop are required"}

            if distance <= 0:

                return {"error": "Distance must be greater than 0"}

            fare = self.cost(distance)        # Fare logic is here so pricing is easy to change later

            ids = self.db.execute("""
                INSERT INTO rides (pickup_location, drop_location, ride_distance, booking_value, booking_status)
                VALUES (?, ?, ?, ?, ?)
            """, (pickup, drop, distance, fare, "booked"))          # Save new ride info and commit the changes to the database

            return {"message": "Ride created", "ride_id": ids, "fare": fare}
        
        except Exception as e:

            return {"error": str(e)}

    def cancel(self, ids):

        try:

            ride = self.db.one(
                "SELECT id FROM rides WHERE id = ?",
                (ids,)
            )

            if not ride:

                return {"error": "Ride not found"}

            self.db.execute(
                "UPDATE rides SET booking_status = 'cancelled' WHERE id = ?",
                (ids,)
            )           # Check so a ride that doesn't exist isnt counted as successful

            return {"message": "Ride cancelled"}
        
        except Exception as e:

            return {"error": str(e)}

    def cost(self, distance):

        fare = 5                    # $5 base for rn
        mile = 2                    # $2 per mile for rn

        return fare + (distance * mile)
