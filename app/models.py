from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ---------------- USER ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

    role = db.Column(db.String(20), nullable=False)   # admin / user


# ---------------- SUBJECT ----------------
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    year = db.Column(db.String(10), nullable=False)
    semester = db.Column(db.Integer, nullable=False)   # ✅ keep int (good)
    section = db.Column(db.String(2), nullable=False)

    subject_name = db.Column(db.String(50), nullable=False)
    teacher = db.Column(db.String(50), nullable=False)

    subject_type = db.Column(db.String(10), nullable=False)  # theory / lab
    hours = db.Column(db.Integer, nullable=False)


# ---------------- TIMETABLE ----------------
class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    day = db.Column(db.String(10), nullable=False)
    period = db.Column(db.Integer, nullable=False)

    year = db.Column(db.String(10), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    section = db.Column(db.String(2), nullable=False)

    subject = db.Column(db.String(50), nullable=False)
    teacher = db.Column(db.String(50), nullable=False)

    class_type = db.Column(db.String(10), nullable=False)  # theory / lab
    room = db.Column(db.String(20), nullable=False)