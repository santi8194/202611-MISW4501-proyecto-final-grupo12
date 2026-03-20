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
        #database_uri = f'sqlite:///{db_path}'
        database_uri = "sqlite:///:memory:"

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
        # Inicializar la configuración de la Saga si no existe
        from Booking.modulos.saga_reservas.infraestructura.dto import SagaDefinitionDTO, SagaStepsDefinitionDTO
        
        if not db.session.query(SagaDefinitionDTO).filter_by(id_flujo="RESERVA_ESTANDAR").first():
            definicion = SagaDefinitionDTO(
                id_flujo="RESERVA_ESTANDAR", 
                version=1, 
                nombre_descriptivo="Flujo actual (Cobro -> Bloqueo PMS -> Revisión Manual)", 
                activo=True
            )
            db.session.add(definicion)

            pasos = [
                SagaStepsDefinitionDTO(index=0, id_flujo="RESERVA_ESTANDAR", version=1, comando="CrearReservaLocalCmd", evento="ReservaCreadaIntegracionEvt", error="ReservaCreadaFalloEvt", compensacion="CancelarReservaLocalCmd"),
                SagaStepsDefinitionDTO(index=1, id_flujo="RESERVA_ESTANDAR", version=1, comando="ProcesarPagoCmd", evento="PagoExitosoEvt", error="PagoRechazadoEvt", compensacion="ReversarPagoCmd"),
                SagaStepsDefinitionDTO(index=2, id_flujo="RESERVA_ESTANDAR", version=1, comando="ConfirmarReservaPmsCmd", evento="ConfirmacionPmsExitosaEvt", error="ReservaRechazadaPmsEvt", compensacion="CancelarReservaPmsCmd"),
                SagaStepsDefinitionDTO(index=3, id_flujo="RESERVA_ESTANDAR", version=1, comando="SolicitarAprobacionManualCmd", evento="ReservaAprobadaManualEvt", error="ReservaRechazadaManualEvt", compensacion=None),
                SagaStepsDefinitionDTO(index=4, id_flujo="RESERVA_ESTANDAR", version=1, comando="ConfirmarReservaLocalCmd", evento="ReservaConfirmadaEvt", error="FallaActualizacionLocalEvt", compensacion="CancelarReservaLocalCmd"),
                SagaStepsDefinitionDTO(index=5, id_flujo="RESERVA_ESTANDAR", version=1, comando="MarcarSagaEsperandoVoucher", evento="VoucherEnviadoEvt", error="FalloEnvioVoucherEvt", compensacion="NotificarFalloTecnicoCmd")
            ]
            db.session.add_all(pasos)
            db.session.commit()
            print("[Booking API] Configuración de Saga Orquestada insertada en BD exitosamente.")

    # Importar y registrar blueprints
    from Booking.modulos.reserva.infraestructura.api import reserva_api
    app.register_blueprint(reserva_api, url_prefix='/api')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
