# placeholder
import json
import math

class DoctorFinder:
    def __init__(self, json_path="data/doctor_data.json"):
        with open(json_path, "r") as f:
            self.doctors = json.load(f)

    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def find_nearest(self, user_lat, user_lon, max_results=3):
        res = []
        for d in self.doctors:
            dist = self.haversine(user_lat, user_lon, d['lat'], d['lon'])
            dcopy = d.copy()
            dcopy['distance_km'] = round(dist, 2)
            res.append(dcopy)
        res.sort(key=lambda x: x['distance_km'])
        return res[:max_results]
