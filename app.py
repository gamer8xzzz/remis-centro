import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'token-seguro-remiseria'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///remiseria.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELOS ---
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    pin = db.Column(db.String(10), unique=True, nullable=False)
    rol = db.Column(db.String(20), default='admin')

class Viaje(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    apellido = db.Column(db.String(80), nullable=False)
    lugar = db.Column(db.String(120), nullable=False) # Origen
    movil = db.Column(db.String(20), nullable=False)
    hora_fin = db.Column(db.String(20), nullable=True)
    desocupa = db.Column(db.String(20), nullable=True) # Destino
    monto = db.Column(db.Float, default=0.0)
    es_tr = db.Column(db.Boolean, default=False) # Transferencia
    es_ab = db.Column(db.Boolean, default=False) # Abonado
    estado = db.Column(db.String(20), default='activo')

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# --- RUTAS ---
@app.route('/')
@login_required
def panel_admin():
    viajes_activos = Viaje.query.filter_by(estado='activo').order_by(Viaje.id.desc()).all()
    return render_template('admin_index.html', viajes=viajes_activos)

@app.route('/registrar_viaje', methods=['POST'])
@login_required
def registrar():
    nuevo = Viaje(
        apellido=request.form.get('apellido'),
        lugar=request.form.get('lugar'),
        movil=request.form.get('movil')
    )
    db.session.add(nuevo)
    db.session.commit()
    return redirect(url_for('panel_admin'))

@app.route('/desocupados')
@login_required
def ver_desocupados():
    pendientes = Viaje.query.filter_by(estado='activo').all()
    finalizados = Viaje.query.filter_by(estado='finalizado').order_by(Viaje.id.desc()).limit(10).all()
    return render_template('desocupados.html', pendientes=pendientes, finalizados=finalizados)

@app.route('/marcar_desocupado/<int:id>', methods=['POST'])
@login_required
def marcar_desocupado(id):
    viaje = Viaje.query.get_or_404(id)
    viaje.hora_fin = datetime.now().strftime("%H:%M")
    viaje.desocupa = request.form.get('lugar_desocupa')
    viaje.monto = float(request.form.get('monto', 0))
    viaje.es_tr = 'es_tr' in request.form
    viaje.es_ab = 'es_ab' in request.form
    viaje.estado = 'finalizado'
    db.session.commit()
    return redirect(url_for('ver_desocupados'))

@app.route('/planillas')
@login_required
def ver_planillas():
    nro_movil = request.args.get('movil')
    viajes_p = []
    if nro_movil:
        viajes_p = Viaje.query.filter_by(movil=nro_movil, estado='finalizado').all()
    return render_template('planillas.html', viajes=viajes_p, nro_movil=nro_movil)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Usuario.query.filter_by(pin=request.form.get('pin')).first()
        if user:
            login_user(user)
            return redirect(url_for('panel_admin'))
        flash('PIN Incorrecto')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Usuario.query.filter_by(pin='1234').first():
            db.session.add(Usuario(nombre='Operador', pin='1234'))
            db.session.commit()
    app.run(debug=True)