
from Payment.modules.payments.application.commands.process_payment import ProcessPayment

def test_successful_payment():
    comando = ProcessPayment()
    evento = comando.execute("reserva123", 200, "USD")
    assert evento is not None