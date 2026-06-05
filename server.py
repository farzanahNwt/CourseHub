#first install: pip install pymongo
import xmlrpc.server
import pymongo
from pymongo import MongoClient

# 1. Database Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["CourseRegistrationDB"]
courses_collection = db["courses"]
registration_collection = db["registrations"]

# 2. View Course Details
def ViewCourse(course_id):
    course = courses_collection.find_one({"course_id": course_id})
    if course:
        return {
            "status": "success", 
            "course_name": course.get("course_name"), 
            "available_seats": course.get("available_seats")
        }
    return {"status": "error", "message": "Course not found"}

# 3. Check Available Seats
def CheckAvailability(course_id):
    course = courses_collection.find_one({"course_id": course_id})
    if course:
        return course.get("available_seats", 0)
    return -1

# 4. Register Student in a Course
def RegisterCourse(student_id, course_id):
    course = courses_collection.find_one({"course_id": course_id})
    if not course:
        return "Course not found"
    
    if course.get("available_seats", 0) <= 0:
        return "No seats available"
    
    already_registered = registration_collection.find_one({"student_id": student_id, "course_id": course_id})
    if already_registered:
        return "Already registered in this course"
    
    courses_collection.update_one({"course_id": course_id}, {"$inc": {"available_seats": -1}})
    registration_collection.insert_one({"student_id": student_id, "course_id": course_id})
    return "Registered successfully"

# 5. Drop Course for a Student
def DropCourse(student_id, course_id):
    registration = registration_collection.find_one({"student_id": student_id, "course_id": course_id})
    if not registration:
        return "You are not registered in this course"
    
    registration_collection.delete_one({"student_id": student_id, "course_id": course_id})
    courses_collection.update_one({"course_id": course_id}, {"$inc": {"available_seats": 1}})
    return "Course dropped successfully"

# 6. Start RPC Server
def start_server():
    server = xmlrpc.server.SimpleXMLRPCServer(("localhost", 50051), allow_none=True)
    print("RPC Server is running on port 50051...")
    
    server.register_function(ViewCourse, "ViewCourse")
    server.register_function(CheckAvailability, "CheckAvailability")
    server.register_function(RegisterCourse, "RegisterCourse")
    server.register_function(DropCourse, "DropCourse")
    
    server.serve_forever()

if __name__ == "__main__":
    start_server()
