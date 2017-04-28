from flask import Flask, render_template, request, session, redirect, url_for
import pymysql.cursors

from appdef import *

#Get the airline the staff member works for
def getStaffAirline():
    username = session['username']
    cursor = conn.cursor()
    #username is a primary key
    query = 'select airline_name from airline_staff where username = %s'
    cursor.execute(query, (username))
    #fetchall returns an array, each element is a dictionary
    airline = cursor.fetchall()[0]['airline_name']
    cursor.close()
    
    return airline

#Make sure that the user is actually staff before performing any operations
def authenticateStaff():
    username = ""
    try:
        #could be that there is no user, make sure
        username = session['username']
    except:
        return False
    
    cursor = conn.cursor()
    query = 'select * from airline_staff where username=%s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    if data:
        return True
    else:
        #Logout before returning error message
        session.pop('username')
        return False

@app.route('/staffHome')
def staffHome():
    if authenticateStaff():
        username = session['username']
        message = request.args.get('message')
        
        return render_template('staff.html', username=username, message=message)
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))
    
@app.route('/staffHome/searchFlights')
def searchFlightsPage():
    if authenticateStaff():
        cursor = conn.cursor()
        
        airline = getStaffAirline()
        
        query = 'select * from flight where airline_name = %s and ((departure_time between curdate() and date_add(curdate(), interval 30 day)) or (arrival_time between curdate() and date_add(curdate(), interval 30 day)))'
        cursor.execute(query, (airline))
        data = cursor.fetchall()
        
        cursor.close()
        
        error = request.args.get('error')
        return render_template('searchStaff.html', error=error, results=data)
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))

@app.route('/staffHome/searchFlights/city', methods=['POST'])
def searchFlightsCity():
    if authenticateStaff():
        cursor = conn.cursor()
        city = request.form['citysearchbox']
        airline = getStaffAirline()
        query = 'select * from flight,airport where (airport.airport_name=flight.departure_airport or airport.airport_name=flight.arrival_airport) and airport.airport_city=%s and airline_name=%s'
        cursor.execute(query, (city, airline))
        data = cursor.fetchall()
        cursor.close()
        error = None
        if data:
            return render_template('searchStaffResults.html', results=data)
        else:
            #returns an error message to the html page
            error = 'No results found'
            return redirect(url_for('searchFlightsPage', error=error))
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))

@app.route('/staffHome/searchFlights/airport', methods=['POST'])
def searchFlightsAirport():
    if authenticateStaff():
        cursor = conn.cursor()
        airport = request.form['airportsearchbox']
        airline = getStaffAirline()
        query = 'select * from flight where (departure_airport = %s or arrival_airport = %s) and airline_name=%s'
        cursor.execute(query, (airport, airport, airline))
        data = cursor.fetchall()
        cursor.close()
        error = None
        if data:
            return render_template('searchStaffResults.html', results=data)
        else:
            #returns an error message to the html page
            error = 'No results found'
            return redirect(url_for('searchFlightsPage', error=error))
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))
    
@app.route('/staffHome/searchFlights/date', methods=['POST'])
def searchFlightsDate():
    if authenticateStaff():
        begintime = request.form['begintime']
        endtime = request.form['endtime']
        airline = getStaffAirline()
        
        cursor = conn.cursor()
        query = 'select * from flight where ((departure_time between %s and %s) or (arrival_time between %s and %s)) and airline_name=%s'
        cursor.execute(query, (begintime, endtime, begintime, endtime, airline))
        data = cursor.fetchall()
        cursor.close()
        error = None
        if data:
            return render_template('searchStaffResults.html', results=data)
        else:
            #returns an error message to the html page
            error = 'No results found'
            return redirect(url_for('searchStaffPage', error=error))
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))
    
@app.route('/staffHome/searchFlights/customers', methods=['POST'])
def searchFlightsCustomer():
    if authenticateStaff():
        flightnum = request.form['flightsearchbox']
        airline = getStaffAirline()
        
        cursor = conn.cursor()
        query = 'select customer_email from purchases natural join ticket where flight_num = %s and airline_name=%s'
        cursor.execute(query, (flightnum, airline))
        data = cursor.fetchall()
        cursor.close()
        if data:
            return render_template('searchStaffResults.html', customerresults=data, flightnum=flightnum)
        else:
            #returns an error message to the html page
            error = 'No results found'
            return redirect(url_for('searchFlightsPage', error=error))
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))
    
@app.route('/staffHome/createFlight')
def createFlightPage():
    if authenticateStaff():
        cursor = conn.cursor()
        query = 'select airport_name from airport'
        cursor.execute(query)
        airportdata = cursor.fetchall()
        
        query = 'select airplane_id from airplane'
        cursor.execute(query)
        airplanedata = cursor.fetchall()
        
        cursor.close()
        
        error = request.args.get('error')
        return render_template('createFlight.html', error=error, airportdata=airportdata, airplanedata=airplanedata)
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))

@app.route('/staffHome/createFlight/Auth', methods=['POST'])
def createFlight():
    if not authenticateStaff():
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))
    
    username = session['username']
    
    flightnum = request.form['flightnum']
    departport = request.form['departport']
    departtime = request.form['departtime']
    arriveport = request.form['arriveport']
    arrivetime = request.form['arrivetime']
    price = request.form['price']
    status = request.form['status']
    airplaneid = request.form['airplanenum']
    airline = getStaffAirline()
    
    #Check that airplane is valid
    cursor = conn.cursor()
    query = 'select * from airplane where airplane_id = %s'
    cursor.execute(query, (airplaneid))
    data = cursor.fetchall()
    if not data:
        error = 'Invalid Airplane ID'
        return redirect(url_for('createFlightPage', error=error))
    
    query = 'insert into flight values (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
    cursor.execute(query, (airline, flightnum, departport, departtime, arriveport, arrivetime, price, status, airplaneid))
    conn.commit()
    cursor.close()
    
    return redirect(url_for('staffHome', message="Operation Successful"))

@app.route('/staffHome/changeFlight')
def changeFlightStatusPage():
    if authenticateStaff():
        error = request.args.get('error')
        return render_template('changeFlight.html', error=error)
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))

@app.route('/staffHome/changeFlight/Auth', methods=['POST'])
def changeFlightStatus():
    if not authenticateStaff():
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))
    
    username = session['username']
    
    flightnum = request.form['flightnum']
    status = request.form['status']
    if not status:
        error = 'Did not select new status'
        return redirect(url_for('changeFlightStatusPage', error=error))
    
    airline = getStaffAirline()
    
    #Check that the flight is from the same airline as the staff
    query = 'select * from flight where flight_num = %s and airline_name = %s'
    cursor.execute(query, (flightnum, airline))
    data = cursor.fetchall()
    if not data:
        error = 'Incorrect permission - can only change flights from your airline'
        return redirect(url_for('changeFlightStatusPage', error=error))
    
    #Update the specified flight
    query = 'update flight set status=%s where flight_num=%s'
    cursor.execute(query, (status, flightnum))
    conn.commit()
    cursor.close()
    
    return redirect(url_for('staffHome', message="Operation Successful"))
    
@app.route('/staffHome/addAirplane')
def addAirplanePage():
    if authenticateStaff():
        error = request.args.get('error')
        return render_template('addAirplane.html', error=error)
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))

@app.route('/staffHome/addAirplane/confirm', methods=['POST'])
def addAirplane():
    if not authenticateStaff():
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))
    
    username = session['username']
    
    planeid = request.form['id']
    seats = request.form['seats']
    airline = getStaffAirline()
    
    #Check if planeid is not taken
    cursor = conn.cursor()
    query = 'select * from airplane where airplane_id = %s'
    cursor.execute(query, (planeid))
    data = cursor.fetchall()
    
    if data:
        error = "Airplane ID already taken"
        return redirect(url_for('addAirplanePage', error=error))
    
    #Insert the airplane
    query = 'insert into airplane values (%s, %s, %s)'
    cursor.execute(query, (airline, planeid, seats))
    conn.commit()
    
    #Get a full list of airplanes
    query = 'select * from airplane where airline_name = %s'
    cursor.execute(query, (airline))
    data = cursor.fetchall()
    cursor.close()
    
    return render_template('addAirplaneConfirm.html', results=data)

@app.route('/staffHome/addAirport')
def addAirportPage():
    if authenticateStaff():
        error = request.args.get('error')
        return render_template('addAirport.html', error=error)
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))

@app.route('/staffHome/addAirport/Auth', methods=['POST'])
def addAirport():
    if not authenticateStaff():
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))
    
    username = session['username']
    
    name = request.form['name']
    city = request.form['city']
    
    cursor = conn.cursor()
    query = 'insert into airport values (%s, %s)'
    cursor.execute(query, (name, city))
    conn.commit()
    cursor.close()
    
    return redirect(url_for('staffHome', message="Operation Successful"))