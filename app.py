from flask import Flask, render_template, request, redirect, url_for
import subprocess
import threading
import os
import csv
import pickle
import numpy as np

app = Flask(__name__)

# Helper functions
def run_add_faces(name, user_id):
    subprocess.run(['python', 'add_faces.py', '--name', name, '--id', user_id])

def run_test():
    subprocess.run(['python', 'test.py'])

# Routes
# Modify home route in app.py
@app.route('/')
def home():
    students_count = 0
    if os.path.exists('data/ids.pkl'):
        with open('data/ids.pkl', 'rb') as f:
            ids = pickle.load(f)
            # Get unique count using set
            students_count = len(set(ids))
    return render_template('home.html', students_count=students_count)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        user_id = request.form['id']
        thread = threading.Thread(target=run_add_faces, args=(name, user_id))
        thread.start()
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/take_attendance')
def take_attendance():
    thread = threading.Thread(target=run_test)
    thread.start()
    return redirect(url_for('home'))

@app.route('/attendance')
def view_attendance():
    attendance_files = []
    if os.path.exists('attendance'):
        attendance_files = os.listdir('attendance')
    return render_template('attendance.html', files=attendance_files)

@app.route('/attendance/<filename>')
def view_attendance_file(filename):
    filepath = os.path.join('attendance', filename)
    if not os.path.exists(filepath):
        return "File not found", 404
    
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        data = list(reader)
    
    return render_template('attendance_file.html', 
                         filename=filename,
                         headers=data[0],
                         records=data[1:])

@app.route('/students')
def list_students():
    students = []
    if os.path.exists('data/ids.pkl') and os.path.exists('data/names.pkl'):
        with open('data/ids.pkl', 'rb') as f:
            ids = pickle.load(f)
        with open('data/names.pkl', 'rb') as f:
            names = pickle.load(f)
        
        unique_students = {}
        for user_id, name in zip(ids, names):
            unique_students[user_id] = name
        students = [{"id": k, "name": v} for k, v in unique_students.items()]
    
    return render_template('students.html', students=students)

@app.route('/remove_student', methods=['POST'])
def remove_student():
    user_id = request.form['id']
    
    # Remove from registration data
    if os.path.exists('data/ids.pkl'):
        try:
            with open('data/ids.pkl', 'rb') as f:
                ids = pickle.load(f)
            with open('data/names.pkl', 'rb') as f:
                names = pickle.load(f)
            with open('data/faces_data.pkl', 'rb') as f:
                faces = pickle.load(f)
        except Exception as e:
            print(f"Error loading data: {e}")
            return redirect(url_for('list_students'))

        # Check data consistency
        if len(ids) != len(names) or (len(ids) != faces.shape[0]):
            print("Data inconsistency detected. IDs, Names, and Faces have mismatched lengths.")
            return redirect(url_for('list_students'))

        indices = [i for i, x in enumerate(ids) if x == user_id]
        
        if not indices:
            print("No entries found for the given user ID.")
            return redirect(url_for('list_students'))

        try:
            new_ids = [id for i, id in enumerate(ids) if i not in indices]
            new_names = [name for i, name in enumerate(names) if i not in indices]
            new_faces = np.delete(faces, indices, axis=0)
        except IndexError as e:
            print(f"Error deleting entries: {e}")
            return redirect(url_for('list_students'))

        # Save updated data
        try:
            with open('data/ids.pkl', 'wb') as f:
                pickle.dump(new_ids, f)
            with open('data/names.pkl', 'wb') as f:
                pickle.dump(new_names, f)
            with open('data/faces_data.pkl', 'wb') as f:
                pickle.dump(new_faces, f)
        except Exception as e:
            print(f"Error saving data: {e}")
            return redirect(url_for('list_students'))

    # Remove from attendance records (existing code remains the same)
    attendance_dir = 'attendance'
    if os.path.exists(attendance_dir):
        for filename in os.listdir(attendance_dir):
            filepath = os.path.join(attendance_dir, filename)
            rows = []
            with open(filepath, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and row[0] != user_id:
                        rows.append(row)
            
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(rows)

    return redirect(url_for('list_students'))

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    os.makedirs("attendance", exist_ok=True)
    app.run(debug=True)