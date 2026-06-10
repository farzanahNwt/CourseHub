# db_functions.py
import pymongo

# Connect to MongoDB
client = pymongo.MongoClient("mongodb+srv://228142User:Farzanah228142@cluster0.6jrmx9v.mongodb.net/")  # Change to your MongoDB URI
db = client["coursehub_db"]
students_col = db["students"]
courses_col = db["courses"]
registrations_col = db["registrations"]

# Function to get available courses
def get_courses():
    return list(courses_col.find())

# Function to register a student to a course
def register_course(student_id, course_id):
    course = courses_col.find_one({"course_id": course_id})
    if not course:
        return False, "Course not found."
    if course['available_seats'] <= 0:
        return False, "No seats available."
    
    # Insert registration
    registrations_col.insert_one({
        "student_id": student_id,
        "course_id": course_id
    })
    
    # Decrease available seats
    courses_col.update_one({"course_id": course_id}, {"$inc": {"available_seats": -1}})
    return True, f"Registered for {course_id}"

# Function to drop a course
def drop_course(student_id, course_id):
    reg = registrations_col.find_one({"student_id": student_id, "course_id": course_id})
    if not reg:
        return False, "You are not registered for this course."
    
    registrations_col.delete_one({"_id": reg["_id"]})
    courses_col.update_one({"course_id": course_id}, {"$inc": {"available_seats": 1}})
    return True, f"Dropped {course_id}"
