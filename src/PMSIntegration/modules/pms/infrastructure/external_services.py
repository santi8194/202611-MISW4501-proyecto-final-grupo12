import random


class PMSMock:

    @staticmethod
    def check_availability(hotel_id, room_type):
        if random.random() < 0.8:
            return True
        return False