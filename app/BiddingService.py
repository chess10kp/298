class BiddingService:
    def __init__(self):
        self.bids= []
        
    def PlaceBid(self, driverID, riderID, fare, distance):
        self.bids.append({"DriverID: " : driverID, "RiderID: " : riderID, "Fare: " : fare, "Distance: " : distance})

    def getBids(self, riderID):
        return [b for b in self.bids if b["RiderID"] == riderID]
    
    def BestBid(self, riderID):
        bids= self.getBids(riderID)
        minimum= bids[0][2] + bids[0][3]
        for b in self.bids:
            if bids[b][2] + bids[b][3] < minimum:
                minimum= bids[b][2] + bids[b][3]
                minBid=bids[b]
        return minBid
