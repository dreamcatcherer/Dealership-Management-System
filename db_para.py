############################################
## Import libraries
############################################

from flask import Flask
from flask_mysqldb import MySQL
import MySQLdb.cursors
from functools import wraps
import re

############################################
## Connecting Flask with MySQL
############################################
app = Flask(__name__)
app.secret_key = 'mysecretkey!@#'  # This is a secret key which you can set whatever you want, but keep it secret. (for extra protection)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'gatechUser'
app.config['MYSQL_PASSWORD'] = 'gatech123'
app.config['MYSQL_DB'] = 'cs6400_fa21_team074'
mysql = MySQL(app)

############################################
## Setting users --get user group list from here
############################################
def get_all_users_list():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # all users --can log in
        cursor.execute('SELECT username FROM user')
        all_users = cursor.fetchall()
        all_users_list = [u['username'] for u in all_users]
    return all_users_list

def get_owner_list():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT username FROM owner')
        all_users = cursor.fetchall()
        all_owner_list = [u['username'] for u in all_users]
    return all_owner_list


def get_manager_list():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT username FROM manager')
        all_users = cursor.fetchall()
        all_manager_list = [u['username'] for u in all_users]
    return all_manager_list

def get_inventoryclerk_list():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT username FROM inventoryclerk')
        all_users = cursor.fetchall()
        all_inventoryclerk_list = [u['username'] for u in all_users]
    return all_inventoryclerk_list

def get_salesperson_list():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT username FROM salesperson')
        all_users = cursor.fetchall()
        all_salesperson_list = [u['username'] for u in all_users]
    return all_salesperson_list

def get_servicewriter_list():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT username FROM servicewriter')
        all_users = cursor.fetchall()
        all_servicewriter_list = [u['username'] for u in all_users]
    return all_servicewriter_list


############################################
## Setting users --get vehicle number for sold/unsold/all
############################################
def get_unsold_vechile_number():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
        SELECT COUNT(vin)AS num_unsold
        FROM vehicle
        WHERE sold_by=\'\';
        """)
        num_unsold_vehicles = cursor.fetchone()
    return num_unsold_vehicles

def get_sold_vechile_number():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
        SELECT COUNT(IFNULL(sold_by,1))AS num_sold
        FROM vehicle
        WHERE sold_by IS NOT NULL;
        """)
        num_sold_vehicles = cursor.fetchone()
    return num_sold_vehicles

def get_all_vechile_number():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
        SELECT COUNT(*)AS num_all
        FROM vehicle
        WHERE sold_by IS NOT NULL;
        """)
        num_all_vehicles = cursor.fetchone()
    return num_all_vehicles

def get_all_individuals():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""SELECT * FROM individual
                       #WHERE driver_id = 
                       """)
        list_individuals = cursor.fetchall()
    return list_individuals

def get_all_business():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""SELECT * FROM business
                      #WHERE driver_id = 
                       """)
        list_business = cursor.fetchall()
    return list_business

def get_all_customerid():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
        SELECT driver_id AS customer_id      
        FROM  individual
        UNION
        SELECT tax_id AS customer_id
        FROM   business
                       """)
        all_customerid = cursor.fetchall()
    return all_customerid



############################################
## get input area of vehicle information--type/manufacturer/color/...
############################################
def get_vehicle_attributes_public():
    """
    get information for drop down menu
    """
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT DISTINCT(manufacturer_name) FROM manufacturer Order by manufacturer_name')
        manufacturer_name = cursor.fetchall()

        cursor.execute('SELECT DISTINCT(model_name) FROM vehicle order by model_name')
        model_name = cursor.fetchall()

        cursor.execute('SELECT DISTINCT(color) FROM color order by color')
        color = cursor.fetchall()

        cursor.execute("""
                    select DISTINCT(case
                       when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
                       when EXISTS(select * from convertible where convertible.vin=vehicle.vin) then 'convertible'
                       when EXISTS(select * from truck where truck.vin=vehicle.vin) then 'truck'
                       when EXISTS(select * from suv where suv.vin=vehicle.vin) then 'suv'
                       when EXISTS(select * from vanorminivan where vanorminivan.vin=vehicle.vin) then 'vanorminivan'
                       else NULL
                      end) as vehicle_type            
                    from vehicle;
                    """)
        vehicle_type = cursor.fetchall()
    return vehicle_type, manufacturer_name, model_name, color



def get_unsold_vehicle_list():

    """
    :return: unsold vehicles information for the table result
    vin/invoice price/ list price/ color/ type/ manufacturer
    """
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
                        select *, format((invoice_price*1.25),2) AS list_price, (case
                           when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
                           when EXISTS(select * from convertible where convertible.vin=vehicle.vin) then 'convertible'
                           when EXISTS(select * from truck where truck.vin=vehicle.vin) then 'truck'
                           when EXISTS(select * from suv where suv.vin=vehicle.vin) then 'suv'
                           when EXISTS(select * from vanorminivan where vanorminivan.vin=vehicle.vin) then 'vanorminivan'
                           else NULL
                          end) as type            
                        from vehicle
                        left join color on vehicle.vin = color.vin
                        left join manufacturer on vehicle.vin = manufacturer.vin
                        where sold_by =\'\'
                        order by vehicle.vin ASC;
                        """)
        unsold_vehicle_list = cursor.fetchall()
    return unsold_vehicle_list



def get_sold_vehicle_list():

    """
    :return: unsold vehicles information for the table result
    vin/invoice price/ list price/ color/ type/ manufacturer
    """
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
                        select *, format((invoice_price*1.25),2) AS list_price, (case
                           when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
                           when EXISTS(select * from convertible where convertible.vin=vehicle.vin) then 'convertible'
                           when EXISTS(select * from truck where truck.vin=vehicle.vin) then 'truck'
                           when EXISTS(select * from suv where suv.vin=vehicle.vin) then 'suv'
                           when EXISTS(select * from vanorminivan where vanorminivan.vin=vehicle.vin) then 'vanorminivan'
                           else NULL
                          end) as type            
                        from vehicle
                        left join color on vehicle.vin = color.vin
                        left join manufacturer on vehicle.vin = manufacturer.vin
                        where sold_by !=\'\'
                        order by vehicle.vin ASC;
                        """)
        sold_vehicle_list = cursor.fetchall()
        # sold_vehicle_list =sold_vehicle_list
    return sold_vehicle_list



def get_all_vehicle_list():

    """
    :return: unsold vehicles information for the table result
    vin/invoice price/ list price/ color/ type/ manufacturer
    """
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
                        select *, format((invoice_price*1.25),2) AS list_price, (case
                           when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
                           when EXISTS(select * from convertible where convertible.vin=vehicle.vin) then 'convertible'
                           when EXISTS(select * from truck where truck.vin=vehicle.vin) then 'truck'
                           when EXISTS(select * from suv where suv.vin=vehicle.vin) then 'suv'
                           when EXISTS(select * from vanorminivan where vanorminivan.vin=vehicle.vin) then 'vanorminivan'
                           else NULL
                          end) as type            
                        from vehicle
                        left join color on vehicle.vin = color.vin
                        left join manufacturer on vehicle.vin = manufacturer.vin
                        order by vehicle.vin ASC;
                        """)
        all_vehicle_list = cursor.fetchall()
    return all_vehicle_list


def get_all_vin_list():

    """
    :return: unsold vehicles information for the table result
    vin/invoice price/ list price/ color/ type/ manufacturer
    """
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
                        select *, format((invoice_price*1.25),2) AS list_price, (case
                           when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
                           when EXISTS(select * from convertible where convertible.vin=vehicle.vin) then 'convertible'
                           when EXISTS(select * from truck where truck.vin=vehicle.vin) then 'truck'
                           when EXISTS(select * from suv where suv.vin=vehicle.vin) then 'suv'
                           when EXISTS(select * from vanorminivan where vanorminivan.vin=vehicle.vin) then 'vanorminivan'
                           else NULL
                          end) as type            
                        from vehicle
                        left join color on vehicle.vin = color.vin
                        left join manufacturer on vehicle.vin = manufacturer.vin
                        order by vehicle.vin ASC;
                        """)
        all_vehicle_list = cursor.fetchall()

        all_vin_list = []
        for d in all_vehicle_list:
            d_vin = d["vin"]
            all_vin_list.append(d_vin)
    return all_vin_list


############################################
## customer informantion
############################################
def get_driverid_list():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
                        select *
                        from individual;
                        """)
        driverid_list = cursor.fetchall()

        all_driverid_list = []
        for d in driverid_list:
            d_driver_id = d["driver_id"]
            all_driverid_list.append(d_driver_id)
    return all_driverid_list