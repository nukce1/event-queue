import logging


class EventHandlerException(Exception):

    def __init__(self, message="Event handler failed."):
        self.message = message
        super().__init__(self.message)


def handle_payment_succeeded(payload: dict) -> None:
    """Stub handler for payment_succeeded events, fails when the payload asks to simulate a failure"""
    if payload.get("simulate_failure", False):
        raise EventHandlerException(message="Simulated failure while handling payment_succeeded event")

    logging.info(f"Handled payment_succeeded event with payload: {payload}")


def handle_refund_issued(payload: dict) -> None:
    """Stub handler for refund_issued events, fails when the payload asks to simulate a failure"""
    if payload.get("simulate_failure", False):
        raise EventHandlerException(message="Simulated failure while handling refund_issued event")

    logging.info(f"Handled refund_issued event with payload: {payload}")


EVENT_HANDLERS = {
    "payment_succeeded": handle_payment_succeeded,
    "refund_issued": handle_refund_issued,
}
