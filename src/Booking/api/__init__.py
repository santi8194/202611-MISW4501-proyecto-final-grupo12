import os
from flask import Flask, jsonify

def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True)

    # Configuración básica
    # Configuración de base de datos dinámica
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME')

    if all([db_user, db_password, db_host, db_name]):
        database_uri = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    else:
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'booking.db'))
        database_uri = f'sqlite:///{db_path}'

    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI=database_uri,
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
        from Booking.config.seed import seed_saga_reservas
        seed_saga_reservas()

    # Importar y registrar blueprints
    from Booking.modulos.reserva.infraestructura.api import reserva_api
    app.register_blueprint(reserva_api, url_prefix='/api')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
