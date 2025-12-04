from flask import Flask, render_template, request, redirect, url_for, flash, session
from Data_Layer.database import Database
from Data_Layer.notification_service import NotificationService
from Application_layer.user_service import UserService
from Data_Layer.queue_service import QueueService
from Data_Layer.inventory_service import InventoryService
from Data_Layer.report_service import ReportService

app = Flask(__name__)
app.secret_key = "supersecret"  # required for sessions

# Backend services
db = Database("data/farmlink_qms.db")
notify = NotificationService(db)
user_svc = UserService(db)
queue_svc = QueueService(db, notify)
inv_svc = InventoryService(db, notify)
report_svc = ReportService(db)

# --- Demo users ---
def ensure_demo_users():
    if not user_svc.get_all():
        user_svc.create_user('Farmer A', 'farmer', 'pass123')
        user_svc.create_user('Rest B', 'restaurant', 'pass123')
        user_svc.create_user('Manager', 'manager', 'admin123')
ensure_demo_users()

# --- Helpers ---
def get_current_user():
    if 'user_id' not in session:
        return None

    return {
        "id": session['user_id'],
        "name": session['user_name'],
        "role": session['role']
    }

# --- Login ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name'].strip()
        password = request.form['password']

        # Verify user
        user = user_svc.verify_user(name, password)  # We'll create this next
        if not user:
            return "Invalid username or password"

        # Store user info in session
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['role'] = user['role']

        # Redirect to main menu
        return redirect(url_for('menu'))

    return render_template('login.html')

# --- Registration ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        role = request.form.get('role').strip()
        password = request.form.get('password').strip()
        
        if not name or not role or not password:
            flash("All fields are required!")
            return redirect(url_for('register'))

        try:
            user_svc.create_user(name, role, password)
            flash("Account created successfully! Please log in.")
            return redirect(url_for('login'))
        except ValueError as ve:
            flash(str(ve))
            return redirect(url_for('register'))

    return render_template('register.html')

# --- Menu ---
@app.route('/menu')
def menu():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template(
        'menu.html',
        user_name=session['user_name'],
        role=session['role']
    )


# --- Queue Submission & Viewing ---
@app.route('/queue')
def queue():
    user = get_current_user()
    
    entries = queue_svc.list_queue_for_user(user)
    
    return render_template(
        'queue.html',
        entries=entries,
        role=user['role']
    )


@app.route('/queue/submit', methods=["POST"])
def submit_queue():
    user = get_current_user()

    item = request.form['item']
    qty = int(request.form['quantity'])

    queue_svc.enqueue(user['id'], item, qty)

    flash("Request submitted!")
    return redirect(url_for('queue'))


@app.route('/queue/process/<int:entry_id>')
def process_entry(entry_id):
    queue_svc.start_processing(entry_id)
    return redirect(url_for('queue'))

@app.route('/queue/done/<int:entry_id>')
def complete_entry(entry_id):
    queue_svc.complete(entry_id)
    return redirect(url_for('queue'))



# --- Notifications ---
@app.route("/notifications")
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    logs = notify.list_for_user(session['user_id'])

    return render_template(
        "notifications.html",
        logs=logs,
        role=session['role']
    )


# --- Inventory ---
@app.route("/inventory", methods=["GET", "POST"])
def inventory():
    if session['role'] != 'manager':
        flash("Access denied")
        return redirect(url_for('menu'))


    items = inv_svc.list_inventory()

    if request.method == "POST" and session['role'] == 'manager':
        name = request.form['name']
        qty = int(request.form['quantity'])
        inv_svc.add_item(name, qty)
        return redirect(url_for('inventory'))

    return render_template("inventory.html", items=items, role=session['role'])


# --- Reports (Manager only) ---
@app.route("/reports")
def reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session['role'] != 'manager':
        flash("Access denied")
        return redirect(url_for('menu'))

    summary = report_svc.summary()
    return render_template(
        "reports.html",
        summary=summary,
        role=session['role']
    )

# --- Logout ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



if __name__ == "__main__":
    app.run(debug=True)
