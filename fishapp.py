from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_marshmallow import Marshmallow
from flask_socketio import SocketIO
from models.components import db, Temperature, PH, DissolvedOxygen, Alert, Feeder, Maintenance, Device

import base64
import cv2
import datetime
import eventlet

app = Flask(__name__, static_folder='static')
app.secret_key = 'temp_key'

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///values.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

socketio = SocketIO(app)
db.init_app(app)
ma = Marshmallow(app)
login_manager = LoginManager()
login_manager.init_app(app)

# Schemas for serialization
class TemperatureSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Temperature

class PHSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = PH

class DissolvedOxygenSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = DissolvedOxygen

def capture_frames(): 
    cap = cv2.VideoCapture(0)
    if not cap.IsOpened():
        return
    while True:
        ret, frame = cap.read()
        if not ret: 
            break
        _, buffer = cv2.imencode('.jpg', frame)
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
        socketio.emit('frame', jpg_as_text)
        eventlet.sleep(0.1)
    cap.release()

# Initialize the database tables (if they don't already exist)
@app.before_request
def create_tables():
    db.create_all()

@app.before_request
def create_sample_user():
    if Device.query.filter_by(device_id="device777").first() is None:
        new_device = Device(device_id="device777")
        new_device.set_password("343")
        db.session.add(new_device)
        db.session.commit()

@login_manager.user_loader
def load_user(device_id):
    return Device.query.get(int(device_id))

# API Routes
@app.route('/set_alias', methods=['POST'])
def update_device_alias():
    new_alias = request.form.get('device-alias-value')
    device = Device.query.first()
    if device:
        device.alias = new_alias
        db.session.commit()
        return jsonify({
            'success': True,
            'alias': device.alias
        })
    else:
        return jsonify({
            'success': False,
            'message': 'No device found to update.'
        })

@app.route('/set_filter', methods=['POST'])
def set_filter():
    new_maintain = Maintenance()
    new_maintain.filter_time = datetime.datetime.now(datetime.timezone.utc)
    new_maintain.water_time = Maintenance.query.order_by(Maintenance.water_time.desc()).first().water_time
    db.session.add(new_maintain)
    db.session.commit()

    formatted_filter_ts = new_maintain.filter_time.strftime('%Y-%m-%d %H:%M:%S')
    formatted_water_ts = 'N/A'
    if (new_maintain.water_time):
        formatted_water_ts = new_maintain.water_time.strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({'filter_ts': formatted_filter_ts, 'water_ts': formatted_water_ts})

@app.route('/set_water', methods=['POST'])
def set_water():
    new_maintain = Maintenance()
    new_maintain.water_time = datetime.datetime.now(datetime.timezone.utc)
    new_maintain.filter_time = Maintenance.query.order_by(Maintenance.filter_time.desc()).first().filter_time
    db.session.add(new_maintain)
    db.session.commit()

    formatted_water_ts = new_maintain.water_time.strftime('%Y-%m-%d %H:%M:%S')
    formatted_filter_ts = 'N/A'
    if (new_maintain.filter_time):
        formatted_filter_ts = new_maintain.filter_time.strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({'filter_ts': formatted_filter_ts, 'water_ts': formatted_water_ts})

@app.route('/set_feeder', methods=['POST'])
def set_feeder():
    new_feeder = Feeder(timestamp=datetime.datetime.now(datetime.timezone.utc))
    db.session.add(new_feeder)
    db.session.commit()

    formatted_timestamp = new_feeder.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({'timestamp': formatted_timestamp})

@app.route('/set_vitals', methods=['POST'])
def set_vitals():
    # get values from form
    temp_set_value = request.form.get('temp-set-value', type=float)
    ph_set_value = request.form.get('ph-set-value', type=float)
    do_set_value = request.form.get('do-set-value', type=float)

    # Update the database with new set values if provided
    if temp_set_value is not None:
        new_temperature = Temperature()
        new_temperature.reported_value = Temperature.query.order_by(Temperature.id.desc()).first().reported_value
        new_temperature.set_value = temp_set_value
        new_temperature.timestamp = datetime.datetime.now(datetime.timezone.utc)
        db.session.add(new_temperature)

    if ph_set_value is not None:
        new_ph = PH()
        new_ph.reported_value = PH.query.order_by(PH.id.desc()).first().reported_value
        new_ph.set_value = ph_set_value
        new_ph.timestamp = datetime.datetime.now(datetime.timezone.utc)
        db.session.add(new_ph)

    if do_set_value is not None:
        new_do = DissolvedOxygen()
        new_do.reported_value = DissolvedOxygen.query.order_by(DissolvedOxygen.id.desc()).first().reported_value
        new_do.set_value = do_set_value
        new_do.timestamp = datetime.datetime.now(datetime.timezone.utc)
        db.session.add(new_do)

    # Commit the changes to the database
    db.session.commit()

    # Retrieve the latest data from the database
    latest_temp = Temperature.query.order_by(Temperature.id.desc()).first()
    latest_ph = PH.query.order_by(PH.id.desc()).first()
    latest_do = DissolvedOxygen.query.order_by(DissolvedOxygen.id.desc()).first()

    # Return updated values as JSON
    return jsonify({
        'latest_temp': {'set_value': latest_temp.set_value if latest_temp else 'N/A'},
        'latest_ph': {'set_value': latest_ph.set_value if latest_ph else 'N/A'},
        'latest_do': {'set_value': latest_do.set_value if latest_do else 'N/A'}
    })

@app.route('/get_vitals', methods=['GET'])
def get_vitals():
    # Ensure the database query runs within the Flask app context
    latest_temp = Temperature.query.order_by(Temperature.timestamp.desc()).first()
    latest_ph = PH.query.order_by(PH.timestamp.desc()).first()
    latest_do = DissolvedOxygen.query.order_by(DissolvedOxygen.timestamp.desc()).first()

    data = {
        'latest_temp': {'reported_value': latest_temp.reported_value if latest_temp else 'N/A'},
        'latest_ph': {'reported_value': latest_ph.reported_value if latest_ph else 'N/A'},
        'latest_do': {'reported_value': latest_do.reported_value if latest_do else 'N/A'}
    }

    return jsonify(data)  # Send the data as a JSON response

@app.route('/set_alert_read/<int:alert_id>', methods=['POST'])
def set_alert_read(alert_id):
    alert = Alert.query.get(alert_id)
    if alert:
        alert.read = True
        db.session.commit()
        return jsonify({'success': True, 'alert_id': alert_id, 'read': alert.read})
    return jsonify({'success': False}), 400  # Return a 400 error if the alert doesn't exist

@app.route('/get_alerts', methods=['GET'])
def get_alerts():
    sort_option = request.args.get('sort', 'timestamp')
    
    if sort_option == 'type_timestamp':
        alerts = Alert.query.order_by(Alert.type.asc(), Alert.timestamp.desc()).all()
    else:
        alerts = Alert.query.order_by(Alert.timestamp.desc()).all()

    alerts_data = [{
        'id': alert.id,
        'title': alert.title,
        'description': alert.description,
        'timestamp': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'read': alert.read,
        'type': alert.type
    } for alert in alerts]

    return jsonify(alerts_data)

@app.route('/delete_alert/<int:alert_id>', methods=['POST'])
def delete_alert(alert_id):
    alert = Alert.query.get(alert_id)
    if alert:
        db.session.delete(alert)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Alert deleted successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Alert not found'}), 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        device_id = request.form['device-id']
        password = request.form['password']

        device = Device.query.filter_by(device_id=device_id).first()

        if device and device.check_password(password):  # In a real app, use hashed passwords
            login_user(device)
            return redirect(url_for('index'))
        else:
            return "Invalid credentials."

    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        logout_user()
        return redirect(url_for('login'))
    return redirect(url_for('index'))

@app.route('/index', methods=['GET'])
@login_required
def index():
    current_device = Device.query.first()
    latest_main = Maintenance.query.order_by(Maintenance.id.desc()).first()
    latest_feed = Feeder.query.order_by(Feeder.timestamp.desc()).first()
    latest_temp = Temperature.query.order_by(Temperature.timestamp.desc()).first()
    latest_ph = PH.query.order_by(PH.timestamp.desc()).first()
    latest_do = DissolvedOxygen.query.order_by(DissolvedOxygen.timestamp.desc()).first()

    if (not latest_main):
        latest_main = Maintenance()
        db.session.add(latest_main)
        db.session.commit()
    if (not latest_feed):
        latest_feed = Feeder()
        db.session.add(latest_feed)
        db.session.commit()
    if (not latest_temp):
        latest_temp = Temperature()
        db.session.add(latest_temp)
        db.session.commit()
    if (not latest_ph):
        latest_ph = PH()
        db.session.add(latest_ph)
        db.session.commit()
    if (not latest_do):
        latest_do = DissolvedOxygen()
        db.session.add(latest_do)
        db.session.commit()

    alerts = Alert.query.order_by(Alert.timestamp.desc()).all()

    return render_template('index.html',
                           current_device=current_device,
                           latest_main=latest_main, latest_feed=latest_feed, 
                           latest_temp=latest_temp, latest_ph=latest_ph, latest_do=latest_do, 
                           alerts=alerts)

if __name__ == '__main__':
    #app.run(debug=True)
    socketio.start_background_task(capture_frames)
    socketio.run(app, debug=True)
