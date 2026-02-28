import os
from flask import Flask, jsonify

def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True)

    # Configuración básica
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'booking.db'))
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI=f'sqlite:///{db_path}',
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    if config_name is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(config_name)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Healthcheck
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({"status": "healthy", "service": "booking"})

    # Base de datos
    from Booking.config.db import db
    db.init_app(app)
    
    # Modelos necesarios para la creación de tablas
    import Booking.modulos.reserva.infraestructura.dto
    import Booking.modulos.saga_reservas.infraestructura.dto
    
    with app.app_context():
        db.create_all()

    # Importar y registrar blueprints
    from Booking.modulos.reserva.infraestructura.api import reserva_api
    app.register_blueprint(reserva_api, url_prefix='/api')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
