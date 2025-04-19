class LocationStore:
    """A simple in-memory store for location data"""
    
    def __init__(self):
        """Initialize the location store"""
        self.locations = {}
        self.next_id = 1
    
    def add_location(self, location_data):
        """Add a new location to the store"""
        location_id = self.next_id
        self.next_id += 1
        
        location = {
            "id": location_id,
            "name": location_data.get("name", ""),
            "description": location_data.get("description", ""),
            "category": location_data.get("category", ""),
            "lat": location_data.get("lat", 0),
            "lng": location_data.get("lng", 0)
        }
        
        self.locations[location_id] = location
        return location_id
    
    def get_location(self, location_id):
        """Get a location by ID"""
        return self.locations.get(location_id)
    
    def update_location(self, location_id, location_data):
        """Update an existing location"""
        if location_id not in self.locations:
            return False
        
        self.locations[location_id].update({
            "name": location_data.get("name", self.locations[location_id]["name"]),
            "description": location_data.get("description", self.locations[location_id]["description"]),
            "category": location_data.get("category", self.locations[location_id]["category"]),
            "lat": location_data.get("lat", self.locations[location_id]["lat"]),
            "lng": location_data.get("lng", self.locations[location_id]["lng"])
        })
        
        return True
    
    def delete_location(self, location_id):
        """Delete a location by ID"""
        if location_id in self.locations:
            del self.locations[location_id]
            return True
        return False
    
    def get_all_locations(self):
        """Get all locations"""
        return list(self.locations.values())
    
    def search_locations(self, query):
        """Search for locations by name"""
        if not query:
            return self.get_all_locations()
        
        query = query.lower()
        return [loc for loc in self.locations.values() 
                if query in loc["name"].lower() or query in loc["description"].lower()]
    
    def filter_locations_by_category(self, category):
        """Filter locations by category"""
        if not category:
            return self.get_all_locations()
        
        return [loc for loc in self.locations.values() 
                if loc["category"].lower() == category.lower()]
    
    def get_all_categories(self):
        """Get a list of all unique categories"""
        return list(set(loc["category"] for loc in self.locations.values()))
