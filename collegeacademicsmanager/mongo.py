from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, render_template, request, redirect, flash
import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env

uri = os.environ.get("url")

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["college_db"]
students = db["students"]
subject = db["subject"]
shop=db["shop"]
app = Flask(__name__)
app.secret_key = os.environ.get('secret_key')

if shop.count_documents({})==0:
    shops = [
        {"name": "MSRIT Stationary", "location": {"type": "Point", "coordinates": [77.7, 12.6]}},  # [lng, lat]
        {"name": "Sapna Book House", "location": {"type": "Point", "coordinates": [77.8, 12.7]}},
        {"name": "Blossom Book Store", "location": {"type": "Point", "coordinates": [77.8, 12.8]}},
        {"name": "Gangarams Book Bureau", "location": {"type": "Point", "coordinates": [78.0, 12.9]}},
        {"name": "Landmark Stationery", "location": {"type": "Point", "coordinates": [78.1, 13.0]}},
        {"name": "Bookworm Bangalore", "location": {"type": "Point", "coordinates": [78.2, 13.1]}},
        {"name": "Premier Stationers", "location": {"type": "Point", "coordinates": [78.3, 13.2]}},
        {"name": "Printo Malleshwaram", "location": {"type": "Point", "coordinates": [78.4, 13.3]}},
        {"name": "Stationery World Indiranagar", "location": {"type": "Point", "coordinates": [78.5, 13.4]}},
        {"name": "Sahitya Bhavan", "location": {"type": "Point", "coordinates": [78.6, 13.5]}}
    ]

    shop.insert_many(shops)
shop.create_index([("location", "2dsphere")])
# Add this after your existing data insertion
if subject.count_documents({}) == 0:
    subject_data = [
        {"branch": "CSE", "subject": "Data Structures"},
        {"branch": "CSE", "subject": "Database Systems"},
        {"branch": "CSE", "subject": "AI"},
        {"branch": "ECE", "subject": "Digital Electronics"},
        {"branch": "ECE", "subject": "Signals & Systems"},
        {"branch": "ECE", "subject": "Embedded Systems"},
        {"branch": "ME", "subject": "Thermodynamics"},
        {"branch": "ME", "subject": "Machine Design"},
        {"branch": "ME", "subject": "CAD/CAM"},
        {"branch": "EEE", "subject": "Power Systems"},
        {"branch": "EEE", "subject": "Control Systems"},
        {"branch": "EEE", "subject": "Electric Machines"},
        {"branch": "CE", "subject": "Structural Engineering"},
        {"branch": "CE", "subject": "Concrete Technology"},
        {"branch": "CE", "subject": "Surveying"}
    ]
    subject.insert_many(subject_data)
if students.count_documents({}) == 0:
    data = [{"name": "Aarav Sharma",
            "usn": "4CSE001",
            "branch": "CSE",
            "semester": 5,
            "cgpa": 8.7,
            "credits_earned": 110,
            "subject1": "Data Structures",
            "subject2": "Database Systems",
            "elective": "AI"},
            {"name": "Ishita Verma",
            "usn": "2ECE002",
            "branch": "ECE",
            "semester": 3,
            "cgpa": 8.3,
            "credits_earned": 70,
            "subject1": "Digital Electronics",
            "subject2": "Signals & Systems",
            "elective": "Embedded Systems"},
            {"name": "Rohan Singh",
            "usn": "2ME034",
            "branch": "ME",
            "semester": 2,
            "cgpa": 4.5,
            "credits_earned": 150,
            "subject1": "Thermodynamics",
            "subject2": "Machine Design",
            "elective": "CAD/CAM"}]
    students.insert_many(data)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_form')
def add_form():
    return render_template('add.html')

@app.route('/add', methods=['POST'])
def add_student():
    name = request.form['name']
    cgpa = float(request.form['cgpa'])
    branch = request.form['branch']
    usn = request.form['usn'].upper()
    semester = int(request.form['semsester'])

    subs = list(subject.find({"branch": branch}, {"_id": 0, "subject": 1}))

    if students.find_one({"usn": usn}):
        flash(f'Student with USN {usn} already exists!', 'error')
        return redirect('/')

    students.insert_one({
        "name": name,
        "cgpa": cgpa,
        "usn": usn,
        "branch": branch,
        "semester": semester,
        "subject1": subs[0]["subject"],
        "subject2": subs[1]["subject"],
        "elective": subs[2]["subject"]
    })

    return redirect('/view')


@app.route('/view')
def view_students():
    all_students = list(students.find())
    return render_template('view.html', students=all_students)


@app.route('/find', methods=['POST'])
def find_student():
    usn = request.form['search_usn'].upper()
    result = students.find_one({"usn": usn})
    return render_template('result.html', student=result)



@app.route('/update', methods=['GET', 'POST'])
def updtelective():
    if request.method == 'GET':
        return render_template('update.html')

    usn = request.form['usn'].upper()
    new = request.form['new_subject']
    students.update_one(
        {"usn": usn},
        {"$set": {"elective": new}}
    )
    return render_template('update.html')


@app.route('/average')
def average_cgpa():
    pipeline = [{"$group": {"_id": None, "avgCGPA": {"$avg": "$cgpa"}}}]
    result = list(students.aggregate(pipeline))
    avg = result[0]['avgCGPA'] if result else 0
    return render_template('average.html', avg=round(avg, 2))


@app.route('/improvements')
def improve():
    low_students = list(db.students.find({"cgpa": {"$lt": 5}}))
    return render_template('improvement.html', students=low_students)

@app.route('/searchnearby',methods=['POST'])
def search():
    lat=float(request.form['latitude'])
    long=float(request.form['longitude'])
    r=int(request.form['range'])
    shops=list(db.shop.find({"location":{"$near":{"$geometry":{"type":"Point","coordinates":[long,lat]},"$maxDistance":r}}}))
    return render_template('places.html',shops=shops,latitude=lat,longitude=long,range=r)

@app.route('/delete',methods=['POST'])
def delete():
    usn=(request.form['usn']).upper()
    db.students.delete_one({"usn":usn})
    return redirect('/view')

if __name__ == '__main__':
    app.run(debug=True)
