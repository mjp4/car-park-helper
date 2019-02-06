import re
import smtplib
import os
import csv

from flask import Flask, request
app = Flask(__name__)

SMTP_ADDRESS = "in-v3.mailjet.com"
SMTP_PORT = 587
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]

@app.route('/', methods=["GET", "POST"])
def car_park_form():
    if request.method == 'POST':
        blocked_cars = [normalise_number_plate(request.form['blocked_car_1']),
                        normalise_number_plate(request.form['blocked_car_2']),
                        normalise_number_plate(request.form['blocked_car_3'])]
        blocked_cars = [car for car in blocked_cars if car]

        for car in blocked_cars:
            send_email_for_reg(request.form['full_name'],
                               request.form['departure_time'],
                               car,
                               comments=request.form['comments'])

        return """
<p>Post successful: {}</p>
<p>You have blocked in: {}</p>
<p>They will be alerted.</p>
        """.format(request.form['full_name'],
                   ", ".join(blocked_cars))

    return """
<h1>Car Park Helper</h1>
<p>Please fill in this form if you are blocking anybody's car in.</p>
<p>They will be alerted by email so that they can contact you if that will be
a problem</p>
<form method=post>
    <p>
        <label for="full_name">Your Full Name</label>
        <input id="full_name" type="text" name="full_name" />
    </p>
    <p>
        <label for="departure_time">When do you plan to leave (HH:MM)</label>
        <input id="departure_time" type="text" name="departure_time" />
    </p>
    <p>
        <label for="blocked_car_1">Blocked Car 1 Registration Number</label>
        <input id="blocked_car_1" type="text" name="blocked_car_1" />
    </p>
    <p>
        <label for="blocked_car_2">Blocked Car 2 Registration Number</label>
        <input id="blocked_car_2" type="text" name="blocked_car_2" />
    </p>
    <p>
        <label for="blocked_car_3">Blocked Car 3 Registration Number</label>
        <input id="blocked_car_3" type="text" name="blocked_car_3" />
    </p>
    <p>
        <label for="comments">Additional comments (e.g. contact preferences)</label>
        <textarea id="comments" name="comments"></textarea>
    <p>
        <input type="submit" value="Submit" />
    </p>
</form>
    """

def normalise_number_plate(reg_num):
    match = re.match(r"^(\w\w)\s?(\d\d)\s?(\w\w\w)$", reg_num)
    if match is not None:
        return "{}{} {}".format(match.group(1).upper(),
                                match.group(2),
                                match.group(3).upper())
    return reg_num


def get_address_from_reg(reg):
    with open("registration_db.csv", "r", newline="") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=("reg", "email"))
        for row in reader:
            if normalise_number_plate(row["reg"]) == reg:
                return row["email"]
    return "mark@perryman.org.uk"


def send_email_for_reg(blocker, departure_time, blocked_reg, comments=""):
    server = smtplib.SMTP(SMTP_ADDRESS, SMTP_PORT)
    server.login(SMTP_USER, SMTP_PASSWORD)

    msg = """
Your car ({}) has been blocked in by {}.  They plan to leave at {}.

Comments: {}
""".format(blocked_reg,
           blocker,
           departure_time,
           comments if comments != "" else "None")
    to_address = get_address_from_reg(blocked_reg)
    server.sendmail("mark@perryman.org.uk", to_address, msg)
