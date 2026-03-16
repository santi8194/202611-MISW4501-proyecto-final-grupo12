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
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validar campos obligatorios
        campos_obligatorios = ['id_usuario', 'id_habitacion', 'monto', 'fecha_reserva']
        for campo in campos_obligatorios:
            if campo not in data or data[campo] is None:
                return jsonify({"error": f"El campo '{campo}' es obligatorio"}), 400

        # Convertimos los strings a UUIDs
        id_usuario = uuid.UUID(data.get('id_usuario'))
        id_habitacion = uuid.UUID(data.get('id_habitacion'))
        monto = float(data.get('monto'))
        fecha_reserva = data.get('fecha_reserva') # Expected YYYY-MM-DD

        comando = CrearReservaHold(
            id_usuario=id_usuario,
            id_habitacion=id_habitacion,
            monto=monto,
            fecha_reserva=fecha_reserva
        )

        uow = UnidadTrabajoHibrida()
        repositorio = RepositorioReservas()
        handler = CrearReservaHoldHandler(repositorio=repositorio, uow=uow)
        
        id_reserva = handler.handle(comando)
        
        return jsonify({"mensaje": "Reserva creada en estado HOLD (15 min)", "id_reserva": str(id_reserva)}), 201

    except Exception as e:
        import traceback
        traceback.print_exc()
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
