from flask import Blueprint, request, jsonify
from Booking.modulos.reserva.aplicacion.comandos import CrearReservaHold, FormalizarReserva
from Booking.modulos.reserva.aplicacion.handlers import CrearReservaHoldHandler, FormalizarReservaHandler
from Booking.modulos.reserva.infraestructura.repositorios import RepositorioReservas
from Booking.config.uow import UnidadTrabajoHibrida
import uuid

reserva_api = Blueprint('reserva_api', __name__)

@reserva_api.route('/reserva', methods=['POST'])
def iniciar_reserva_hold():
    try:
        data = request.json
        # Convertimos los strings a UUIDs
        id_usuario = uuid.UUID(data.get('id_usuario'))
        id_habitacion = uuid.UUID(data.get('id_habitacion'))
        monto = float(data.get('monto'))

        comando = CrearReservaHold(
            id_usuario=id_usuario,
            id_habitacion=id_habitacion,
            monto=monto
        )

        uow = UnidadTrabajoHibrida()
        repositorio = RepositorioReservas()
        handler = CrearReservaHoldHandler(repositorio=repositorio, uow=uow)
        
        id_reserva = handler.handle(comando)
        
        return jsonify({"mensaje": "Reserva creada en estado HOLD (15 min)", "id_reserva": str(id_reserva)}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@reserva_api.route('/reserva/<id_reserva>/formalizar', methods=['POST'])
def formalizar_reserva(id_reserva):
    try:
        comando = FormalizarReserva(id_reserva=uuid.UUID(id_reserva))
        
        uow = UnidadTrabajoHibrida()
        repositorio = RepositorioReservas()
        handler = FormalizarReservaHandler(repositorio=repositorio, uow=uow)
        
        handler.handle(comando)

        return jsonify({"mensaje": "Reserva formalizada. Iniciando SAGA de confirmación con Hoteles y Pagos"}), 200

    except ValueError as e:
         return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
