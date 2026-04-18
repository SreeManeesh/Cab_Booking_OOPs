import random

drivers_data = {
    "mini": {
        "name": "Sanjay Vikas",
        "phone": "9876543210",
        "vehicle": "AP09 AB 1234",
        "car": "Swift"
    },
    "sedan": {
        "name": "Satyanarayana",
        "phone": "9123456780",
        "vehicle": "AP28 CD 5678",
        "car": "Dzire"
    },
    "suv": {
        "name": "Bhanu vikas",
        "phone": "9012345678",
        "vehicle": "AP05 EF 9999",
        "car": "Innova"
    }
}

class Ride:
    def calculate_fare(self, distance):
        return 0


class MiniRide(Ride):
    def calculate_fare(self, distance):
        return 50 + distance * 10


class SedanRide(Ride):
    def calculate_fare(self, distance):
        return 80 + distance * 15


class SUVRide(Ride):
    def calculate_fare(self, distance):
        return 100 + distance * 20


class CashPayment:
    def pay(self, amount):
        print(f"Paid ₹{amount} using Cash")


class UPIPayment:
    def pay(self, amount):
        print(f"Paid ₹{amount} using UPI")


class Booking:
    def __init__(self, ride_type, distance, fare, pickup, drop, driver):
        self.booking_id = random.randint(1000, 9999)
        self.ride_type = ride_type
        self.distance = distance
        self.fare = fare
        self.pickup = pickup
        self.drop = drop
        self.driver = driver

    def show_details(self):
        print("\n --- Driver & Vehicle Details ---")
        print("Driver Name:", self.driver["name"])
        print("Phone:", self.driver["phone"])
        print("Car:", self.driver["car"])
        print("Vehicle No:", self.driver["vehicle"])

        print("\n --- Ride Details ---")
        print("Booking ID:", self.booking_id)
        print("Ride Type:", self.ride_type)
        print("Pickup:", self.pickup)
        print("Drop:", self.drop)
        print("Distance:", self.distance, "km")
        print("Total Fare: ₹", self.fare)


while True:

    pickup = input("\nEnter Pickup Location: ")
    drop = input("Enter Drop Location: ")
    distance = float(input("Enter distance (km): "))

    ride_choice = input("Choose ride (mini/sedan/suv): ").lower()

    if ride_choice == "mini":
        ride = MiniRide()
    elif ride_choice == "sedan":
        ride = SedanRide()
    elif ride_choice == "suv":
        ride = SUVRide()
    else:
        print("Invalid ride type")
        continue

    fare = round(ride.calculate_fare(distance))

    driver = drivers_data[ride_choice]

    booking = Booking(ride_choice, distance, fare, pickup, drop, driver)
    booking.show_details()

    mode = input("\nChoose payment (cash/upi): ").lower()

    if mode == "cash":
        payment = CashPayment()
    elif mode == "upi":
        payment = UPIPayment()
    else:
        print("Invalid payment method")
        continue

    payment.pay(booking.fare)

    again = input("\nDo you want another booking? (yes/no): ").lower()
    if again != "yes":
        print("Thank you for using Cab Service ")
        break