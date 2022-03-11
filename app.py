############################################
## Import libraries
############################################

from flask import Flask, render_template, request, redirect, url_for, session, flash, json
from flask_mysqldb import MySQL
import MySQLdb.cursors
from functools import wraps
import db_para as db_para
from datetime import date
from db_para import get_all_users_list, get_owner_list, get_manager_list, \
    get_inventoryclerk_list, get_salesperson_list, get_servicewriter_list, \
    get_unsold_vechile_number, get_sold_vechile_number, get_vehicle_attributes_public, \
    get_unsold_vehicle_list, get_sold_vehicle_list, get_all_vehicle_list, get_all_vin_list, \
    get_driverid_list,get_all_customerid

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
## Setting login page
############################################


# check if user logged in
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))

    return wrap


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE username = % s AND password = % s', (username, password))
        user = cursor.fetchone()
        if user:
            session['logged_in'] = True
            session['username'] = user['username']
            return redirect(url_for('loggedin_home'))
        else:
            msg = "Incorrect username / password !"
    return render_template('login.html', msg=msg)


############################################
## Anonymous user search page
############################################
@app.route('/anonymous_search/', methods=['GET', 'POST'])
def anonymous_search():
    vehicle_type, manufacturer_name, model_name, color = get_vehicle_attributes_public()
    num_unsold_vehicles = get_unsold_vechile_number()
    return render_template('anonymous_search.html',
                           vehicle_type=vehicle_type,
                           manufacturer_name=manufacturer_name,
                           model_name=model_name,
                           color=color,
                           num_unsold_vehicles=num_unsold_vehicles
                           )


@app.route('/anonymous_search/anonymous_search_result/', methods=['GET', 'POST'])
def anonymous_search_result():
    msg = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        vehicle_type = request.form.get('vehicle_type')

        manufacturer_name = request.form.get('manufacturer_name')

        model_name = request.form.get('model_name')

        model_year = request.form.get('model_year')

        color = request.form.get('color')

        list_price = request.form.get('list_price')
        comp_select = request.form.get('comp_select')

        keyword = request.form.get('keyword')

        # 1. get the all the information of unsold vehicles (tested correct--77 vehicles)
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
            where sold_by=""
            order by vehicle.vin ASC;
            """)

        # cursor.execute('select * from vehicle where sold_by =\'\' ')

        vehicle_list = cursor.fetchall()

        vinlist = sorted([v['vin'] for v in vehicle_list])  # get all unsold vin list (77)

        # 2. get the number of unsold vehicles
        num_unsold_vehicles = get_unsold_vechile_number()  # 77

        # 3. search part loop in unsold vehicles
        if not (vehicle_type or manufacturer_name or model_name or model_year or color or list_price or keyword):
            msg = 'Not valid input info'

        if manufacturer_name != "":
            cursor.execute("""
            SELECT *, format((invoice_price*1.25),2) AS list_price
            FROM vehicle
            left join manufacturer on vehicle.vin = manufacturer.vin
            WHERE manufacturer_name = %s
            AND sold_by =\'\'
            """, (manufacturer_name,))
            vehicle_list2 = cursor.fetchall()
            vinlist2 = [v['vin'] for v in vehicle_list2]

            if vinlist:
                vinlist = list(ele1 for ele1 in vinlist for ele2 in vinlist2 if ele1 == ele2)
            else:
                vinlist = vinlist2

        if color != "":
            cursor.execute("""
                        SELECT *, format((invoice_price*1.25),2) AS list_price
                        FROM vehicle
                        left join color on vehicle.vin = color.vin
                        WHERE color = %s
                        AND sold_by =\'\'
                        """, (color,))
            vehicle_list2 = cursor.fetchall()
            vinlist2 = [v['vin'] for v in vehicle_list2]
            if vinlist:
                vinlist = list(ele1 for ele1 in vinlist for ele2 in vinlist2 if ele1 == ele2)
            else:
                vinlist = vinlist2

        if model_name != "":

            cursor.execute("""
                        SELECT *, format((invoice_price*1.25),2) AS list_price
                        FROM vehicle
                        WHERE model_name = %s
                        AND sold_by =\'\';
                        """, (model_name,))
            vehicle_list2 = cursor.fetchall()
            vinlist2 = [v['vin'] for v in vehicle_list2]
            if vinlist:
                vinlist = list(ele1 for ele1 in vinlist for ele2 in vinlist2 if ele1 == ele2)
            else:
                vinlist = vinlist2

        if model_year != "":

            model_year = int(model_year)
            cursor.execute("""
                        SELECT *, format((invoice_price*1.25),2) AS list_price
                        FROM vehicle
                        WHERE model_year = % s
                        AND sold_by =\'\';
                        """, (model_year,))
            vehicle_list2 = cursor.fetchall()
            vinlist2 = [v['vin'] for v in vehicle_list2]
            if vinlist:
                vinlist = list(ele1 for ele1 in vinlist for ele2 in vinlist2 if ele1 == ele2)
            else:
                vinlist = vinlist2

        if list_price != "":
            if comp_select == "greaterthan":
                cursor.execute("""
                                SELECT *, format((invoice_price*1.25),2) AS list_price
                                FROM vehicle
                                WHERE invoice_price*1.25 > % s
                                AND sold_by =\'\'
                                """, (list_price,))
                vehicle_list2 = cursor.fetchall()
                vinlist2 = [v['vin'] for v in vehicle_list2]
                if vinlist:
                    vinlist = list(ele1 for ele1 in vinlist for ele2 in vinlist2 if ele1 == ele2)
                else:
                    vinlist = vinlist2

            if comp_select == "lessthan":
                cursor.execute("""
                                SELECT *, format((invoice_price*1.25),2) AS list_price
                                FROM vehicle
                                WHERE invoice_price*1.25 < % s
                                AND sold_by =\'\'
                                """, (list_price,))
                vehicle_list2 = cursor.fetchall()
                vinlist2 = [v['vin'] for v in vehicle_list2]
                if vinlist:
                    vinlist = list(ele1 for ele1 in vinlist for ele2 in vinlist2 if ele1 == ele2)
                else:
                    vinlist = vinlist2

        if vehicle_type != "":
            cursor.execute("""
                    with typeAdded as
                        (SELECT vin, format((invoice_price*1.25),2) AS list_price,
                            case
                                when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
                                when EXISTS(select * from convertible where convertible.vin=vehicle.vin) then 'convertible'
                                when EXISTS(select * from truck where truck.vin=vehicle.vin) then 'truck'
                                when EXISTS(select * from suv where suv.vin=vehicle.vin) then 'suv'
                                when EXISTS(select * from vanorminivan where vanorminivan.vin=vehicle.vin) then 'vanorminivan'
                                else \"\"
                        end as v_type,sold_by
                        FROM vehicle)
                    select *
                    from typeAdded
                    where v_type = %s
                    And sold_by=\'\'
                        """, (vehicle_type,))
            vehicle_list2 = cursor.fetchall()
            vinlist2 = [v['vin'] for v in vehicle_list2]

            if vinlist:
                vinlist = list(ele1 for ele1 in vinlist for ele2 in vinlist2 if ele1 == ele2)
            else:
                vinlist = vinlist2

        if keyword != "":

            cursor.execute("""
                    select *,format((invoice_price*1.25),2) AS list_price
                    from vehicle v
                    inner join manufacturer m on v.vin = m.vin
                    where sold_by=\'\' and (description like %s or m.manufacturer_name like %s
                    or model_name like %s or model_year like %s)
                          """
                           , (
                           {'%' + keyword + '%'}, {'%' + keyword + '%'}, {'%' + keyword + '%'}, {'%' + keyword + '%'},))


            vehicle_list2 = cursor.fetchall()
            vinlist2 = [v['vin'] for v in vehicle_list2]

            if vinlist:
                vinlist = list(ele1 for ele1 in vinlist for ele2 in vinlist2 if ele1 == ele2)
            else:
                vinlist = vinlist2

        # print("finally vinlist:")
        # print(vinlist)

        data = []
        for item in list(vinlist):
            cursor.execute("""
            with typeAdded as
                (SELECT *, format((invoice_price*1.25),2) AS list_price,
                case
                   when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
                   when EXISTS(select * from convertible where convertible.vin=vehicle.vin) then 'convertible'
                   when EXISTS(select * from truck where truck.vin=vehicle.vin) then 'truck'
                   when EXISTS(select * from suv where suv.vin=vehicle.vin) then 'suv'
                   when EXISTS(select * from vanorminivan where vanorminivan.vin=vehicle.vin) then 'vanorminivan'
                   else ""
                end as v_type
                FROM vehicle)
            select *
            from typeAdded v
            inner join color c on v.vin =c.vin
            inner join manufacturer m on v.vin=m.vin
            where v.vin=%s
            """, (item,))
            rst_one = cursor.fetchone()
            data.append(rst_one)
        # print(data)

        #     cursor.execute("""
        #     select *, format((invoice_price * 1.25), 2) AS
        #     list_price, (case
        #                  when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
        #                  when EXISTS(select * from convertible where convertible.vin = vehicle.vin) then 'convertible'
        #                  when EXISTS(select * from truck where truck.vin = vehicle.vin) then 'truck'
        #                  when EXISTS(select * from suv where suv.vin = vehicle.vin) then 'suv'
        #                  when EXISTS(select * from vanorminivan where vanorminivan.vin = vehicle.vin) then 'vanorminivan'
        #                  else NULL
        #                  end) as type
        #     from vehicle
        #     left join color on vehicle.vin = color.vin
        #     left join manufacturer on vehicle.vin = manufacturer.vin
        #     WHERE vehicle.vin = % s
        #     AND sold_by IS NULL
        #     order by vehicle.vin ASC;
        #     """, (item,))

        #     resultdict = cursor.fetchone()
        #     data.append(resultdict)

        # print("data:", data)

        # cursor.execute("""
        # select *, format((invoice_price*1.25),2) AS list_price, (case
        #        when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
        #        when EXISTS(select * from convertible where convertible.vin=vehicle.vin) then 'convertible'
        #        when EXISTS(select * from truck where truck.vin=vehicle.vin) then 'truck'
        #        when EXISTS(select * from suv where suv.vin=vehicle.vin) then 'suv'
        #        when EXISTS(select * from vanorminivan where vanorminivan.vin=vehicle.vin) then 'vanorminivan'
        #        else NULL
        #       end) as type
        #     from vehicle
        #     left join color on vehicle.vin = color.vin
        #     left join manufacturer on vehicle.vin = manufacturer.vin
        #     where model_name= %s
        #     and model_year= %s
        #     and sold_by IS NOT NULL
        #     having type= %s
        #     and color= %s
        #     and manufacturer_name= %s
        #     and list_price<=%s  or list_price>%s
        #     # OR (
        #     #     manufacturer_name LIKE %s
        #     #     OR model_year LIKE %s
        #     #     OR model_name LIKE %s
        #     #     OR description LIKE %s
        #     #     )
        #     order by vehicle.vin ASC;
        # """, (model_name, model_year, vehicle_type, color, manufacturer_name, list_price, ))
        # data = cursor.fetchall()

        # num_unsold_vehicles=0
        # vehicle_list=[]
        # data=[]
        # print("leave anonymous_search")
        sorted(data, key=lambda i: i['vin'])
        # print(data)

        return render_template('anonymous_search_result.html',
                               msg=msg,
                               # vehicle_list=vehicle_list,
                               num_unsold_vehicles=num_unsold_vehicles["num_unsold"],
                               data=data)


############################################
## Home Page -- this is only accessible for the loggedin users
############################################
@app.route('/loggedin_home/')
@login_required
def loggedin_home():
    ## get the current user and the authorized uses to perform functionality on adding new vehicles
    user = session['username']
    # ----modify starts from here 11/25----
    inventoryclerk_list = get_inventoryclerk_list()

    return render_template('loggedin_home_base.html',
                           user=user,
                           inventoryclerk_list=inventoryclerk_list
                           )


@app.route('/loggedin_home/profile/')
@login_required
def profile():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM user WHERE username = %s', [session['username']])
    user = cursor.fetchone()  # current user
    # modify here for user group  11-27
    inventoryclerk_list = get_inventoryclerk_list()
    servicewriter_list = get_servicewriter_list()
    salesperson_list = get_salesperson_list()
    manager_list = get_manager_list()
    return render_template('profile.html',
                           user=user,
                           inventoryclerk_list=inventoryclerk_list,
                           servicewriter_list=servicewriter_list,
                           salesperson_list=salesperson_list,
                           manager_list=manager_list
                           )


############################################
## Inventory page
############################################
@app.route('/loggedin_home/inventory/')
@login_required
def inventory():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    ## get the current user
    user = session['username']
    # check if the user is inventoryclerk
    inventoryclerk_list = get_inventoryclerk_list()

    # get number of unsold vehicles
    num_unsold_vehicles = get_unsold_vechile_number()

    # get unsold vehicle list
    unsold_vehicle_list = get_unsold_vehicle_list()

    # 1. get the all the information of unsold vehicles (tested correct--77 vehicles)
    vehicle_list = get_unsold_vehicle_list()
    vinlist = {v['vin'] for v in vehicle_list}  # get all unsold vin list

    vehicle_type, manufacturer_name, model_name, color = get_vehicle_attributes_public()

    # search loop start from here 11/25 modified
    # if vin:
    #     cursor.execute("""
    #     SELECT *
    #     FROM Vehicle
    #     WHERE vin = % s
    #     AND sold_by IS NULL
    #     """, (vin,))
    #     vehicle_list = cursor.fetchall()
    #     vinlist = {v['vin'] for v in vehicle_list}

    return render_template('inventory.html',
                           manufacturer_name=manufacturer_name,
                           model_name=model_name,
                           vehicle_type=vehicle_type,
                           color=color,
                           vehicle_list=vehicle_list,
                           num_unsold_vehicles=num_unsold_vehicles,
                           user=user,
                           inventoryclerk_list=inventoryclerk_list,
                           unsold_vehicle_list=unsold_vehicle_list
                           )


@app.route('/loggedin_home/inventory/advanced_search_inventory/', methods=['GET', 'POST'])
@login_required
def advanced_search_inventory():
    # print(session['username'])
    inventoryclerk_list = get_inventoryclerk_list()
    manager_list = get_manager_list()

    ## get the current user and the authorized uses to perform functionality on editing and deleting
    user = session['username']

    salespeople_list = get_salesperson_list()  # can sell the vehicle
    owner_list = get_owner_list()
    today = date.today()
    curr_date = today.strftime("%Y-%m-%d")
    msg = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # if request.method == 'POST' and (user in owner_list or user in salespeople_list):
    if request.method == 'POST':
        vin = request.form.get('s_vin')  # anonymous user cannot use vin to search
        # print("vin " + vin)
        vehicle_type = request.form.get('s_vehicle_type')
        # print("vehicle_type " + vehicle_type)
        manufacturer_name = request.form.get('manufacturer_name')
        # print("manufacturer_name " + manufacturer_name  )
        model_name = request.form.get('model_name')
        # print("model_name " + model_name)
        model_year = request.form.get('model_year')
        # print("model_year " + model_year)
        # print(model_year + "YYYYYYYY")
        color = request.form.get('color')
        # print("color " + color)
        list_price = request.form.get('list_price')
        comp_select = request.form.get('comp_select')
        # print("list_price "  + list_price)
        keyword = request.form.get('Keyword')
        # print("keyword " + keyword)
        min_sold_price = {}

        # 1. get the all the information of unsold vehicles (tested correct--77 vehicles)
        cursor.execute('select * from vehicle where sold_by =\'\' ')
        vehicle_list = cursor.fetchall()
        cursor.execute('select * from vehicle where sold_by <>\'\' ')
        vehicle_list_sold = cursor.fetchall()
        cursor.execute('select * from vehicle ')
        vehicle_list_all = cursor.fetchall()

        vinlist = sorted([v['vin'] for v in vehicle_list])  # get all unsold vin list (77)
        vinlist_sold = sorted([v['vin'] for v in vehicle_list_sold])
        vinlist_all = sorted([v['vin'] for v in vehicle_list_all])
        # 2. get the number of unsold vehicles
        num_unsold_vehicles = get_unsold_vechile_number()  # 77

        # 3. search part loop in unsold vehicles
        if not (vin or vehicle_type or manufacturer_name or model_name or model_year or color or list_price or keyword):
            msg = 'Not valid input info'
       
        if vin != "":
            #unsold
            cursor.execute("""
            SELECT *
            FROM vehicle v
            left join manufacturer on v.vin = manufacturer.vin
            WHERE v.vin = %s
            AND sold_by =\'\'
            """, (vin,))
            vehicle_list2 = cursor.fetchall()
            vinlist2 = {v['vin'] for v in vehicle_list2}


            if vinlist:
                vinlist = list(ele1 for ele1 in vinlist for ele2 in vinlist2 if ele1 == ele2)
            else:
                vinlist = vinlist2
            #sold
            cursor.execute("""
            SELECT *
            FROM vehicle v
            left join manufacturer on v.vin = manufacturer.vin
            WHERE v.vin = %s
            AND sold_by <>\'\'
            """, (vin,))
            vehicle_list_sold2 = cursor.fetchall()
            vinlist_sold2 = {v['vin'] for v in vehicle_list_sold2}


            if vinlist_sold:
                vinlist_sold = list(ele1 for ele1 in vinlist_sold for ele2 in vinlist_sold2 if ele1 == ele2)
            else:
                vinlist_sold = vinlist_sold2
            #all
            cursor.execute("""
            SELECT *
            FROM vehicle v
            left join manufacturer on v.vin = manufacturer.vin
            WHERE v.vin = %s
            
            """, (vin,))
            vehicle_list_all2 = cursor.fetchall()
            vinlist_all2 = {v['vin'] for v in vehicle_list_all2}


            if vinlist_all:
                vinlist_all = list(ele1 for ele1 in vinlist_all for ele2 in vinlist_all2 if ele1 == ele2)
            else:
                vinlist_all = vinlist_all2

        



        if manufacturer_name != "":
             #unsold
            cursor.execute("""
            SELECT *
            FROM vehicle
            left join manufacturer on vehicle.vin = manufacturer.vin
            WHERE manufacturer_name = %s
            AND sold_by =\'\'
            """, (manufacturer_name,))
            vehicle_list2 = cursor.fetchall()
            vinlist2 = {v['vin'] for v in vehicle_list2}


            if vinlist:
                vinlist = list(ele1 for ele1 in vinlist for ele2 in vinlist2 if ele1 == ele2)
            else:
                vinlist = vinlist2
            #sold

            cursor.execute("""
            SELECT *
            FROM vehicle
            left join manufacturer on vehicle.vin = manufacturer.vin
            WHERE manufacturer_name = %s
            AND sold_by <>\'\'
            """, (manufacturer_name,))
            vehicle_list_sold2 = cursor.fetchall()
            vinlist_sold2 = {v['vin'] for v in vehicle_list_sold2}


            if vinlist_sold:
                vinlist_sold = list(ele1 for ele1 in vinlist_sold for ele2 in vinlist_sold2 if ele1 == ele2)
            else:
                vinlist_sold = vinlist_sold2
             #all
            cursor.execute("""
            SELECT *
            FROM vehicle
            left join manufacturer on vehicle.vin = manufacturer.vin
            WHERE manufacturer_name = %s
            
            """, (manufacturer_name,))
            vehicle_list_all2 = cursor.fetchall()
            vinlist_all2 = {v['vin'] for v in vehicle_list_all2}


            if vinlist_all:
                vinlist_all = list(ele1 for ele1 in vinlist_all for ele2 in vinlist_all2 if ele1 == ele2)
            else:
                vinlist_all = vinlist_all2

        if color != "":
             #unsold
            cursor.execute("""
                        SELECT *
                        FROM vehicle
                        left join color on vehicle.vin = color.vin
                        WHERE color = %s
                        AND sold_by =\'\'
                        """, (color,))
            vehicle_list2 = cursor.fetchall()
            vinlist2 = [v['vin'] for v in vehicle_list2]

            if vinlist:
                vinlist = list(ele1 for ele1 in vinlist for ele2 in vinlist2 if ele1 == ele2)
            else:
                vinlist = vinlist2

            #sold
            cursor.execute("""
                        SELECT *
                        FROM vehicle
                        left join color on vehicle.vin = color.vin
                        WHERE color = %s
                        AND sold_by <>\'\'
                        """, (color,))
            vehicle_list_sold2 = cursor.fetchall()
            vinlist2_sold = [v['vin'] for v in vehicle_list_sold2]

            if vinlist_sold:
                vinlist_sold = list(ele1 for ele1 in vinlist_sold for ele2 in vinlist_sold2 if ele1 == ele2)
            else:
                vinlist_sold = vinlist_sold2

            #all
            cursor.execute("""
                        SELECT *
                        FROM vehicle
                        left join color on vehicle.vin = color.vin
                        WHERE color = %s
                        AND sold_by <>\'\'
                        """, (color,))
            vehicle_list_all2 = cursor.fetchall()
            vinlist2_all = [v['vin'] for v in vehicle_list_all2]

            if vinlist_all:
                vinlist_all = list(ele1 for ele1 in vinlist_all for ele2 in vinlist_all2 if ele1 == ele2)
            else:
                vinlist_all = vinlist_all2

        if model_name != "":
             #unsold
            cursor.execute("""
                        SELECT *
                        FROM vehicle
                        WHERE model_name = %s
                        AND sold_by =\'\';
                        """, (model_name,))
            vehicle_list2 = cursor.fetchall()
            vinlist2 = [v['vin'] for v in vehicle_list2]

            if vinlist:
                vinlist = list(ele1 for ele1 in vinlist for ele2 in vinlist2 if ele1 == ele2)
            else:
                vinlist = vinlist2
            #sold

            cursor.execute("""
                        SELECT *
                        FROM vehicle
                        WHERE model_name = %s
                        AND sold_by <>\'\';
                        """, (model_name,))
            vehicle_list_sold2 = cursor.fetchall()
            vinlist_sold2 = [v['vin'] for v in vehicle_list_sold2]

            if vinlist_sold:
                vinlist_sold = list(ele1 for ele1 in vinlist_sold for ele2 in vinlist_sold2 if ele1 == ele2)
            else:
                vinlist_sold = vinlist_sold2
            #all

            cursor.execute("""
                        SELECT *
                        FROM vehicle
                        WHERE model_name = %s
                       
                        """, (model_name,))
            vehicle_list_all2 = cursor.fetchall()
            vinlist_all2 = [v['vin'] for v in vehicle_list_all2]

            if vinlist_all:
                vinlist_all = list(ele1 for ele1 in vinlist_all for ele2 in vinlist_all2 if ele1 == ele2)
            else:
                vinlist_all = vinlist_all2

        if model_year != "":
             #unsold
            model_year = int(model_year)
            cursor.execute("""
                        SELECT *
                        FROM vehicle
                        WHERE model_year = % s
                        AND sold_by =\'\';
                        """, (model_year,))
            vehicle_list2 = cursor.fetchall()
            vinlist2 = [v['vin'] for v in vehicle_list2]


            if vinlist:
                vinlist = list(ele1 for ele1 in vinlist for ele2 in vinlist2 if ele1 == ele2)
            else:
                vinlist = vinlist2
            #sold
            model_year = int(model_year)
            cursor.execute("""
                        SELECT *
                        FROM vehicle
                        WHERE model_year = % s
                        AND sold_by <>\'\';
                        """, (model_year,))
            vehicle_list_sold2 = cursor.fetchall()
            vinlist_sold2 = [v['vin'] for v in vehicle_list_sold2]


            if vinlist_sold:
                vinlist_sold = list(ele1 for ele1 in vinlist_sold for ele2 in vinlist_sold2 if ele1 == ele2)
            else:
                vinlist_sold = vinlist_sold2
            #all
            model_year = int(model_year)
            cursor.execute("""
                        SELECT *
                        FROM vehicle
                        WHERE model_year = % s

                        """, (model_year,))
            vehicle_list_all2 = cursor.fetchall()
            vinlist_all2 = [v['vin'] for v in vehicle_list_all2]


            if vinlist_all:
                vinlist_all = list(ele1 for ele1 in vinlist_all for ele2 in vinlist_all2 if ele1 == ele2)
            else:
                vinlist_all = vinlist_all2
            
        if list_price != "":
             #unsold
            if comp_select == "greaterthan":
                cursor.execute("""
                                        SELECT *
                                        FROM vehicle
                                        WHERE invoice_price*1.25 > % s
                                        AND sold_by =\'\'
                                        """, (list_price,))
                vehicle_list2 = cursor.fetchall()
                vinlist2 = [v['vin'] for v in vehicle_list2]
                if vinlist:
                    vinlist = list(ele1 for ele1 in vinlist for ele2 in vinlist2 if ele1 == ele2)
                else:
                    vinlist = vinlist2

            if comp_select == "lessthan":
                cursor.execute("""
                                        SELECT *
                                        FROM vehicle
                                        WHERE invoice_price*1.25 < % s
                                        AND sold_by =\'\'
                                        """, (list_price,))
                vehicle_list2 = cursor.fetchall()
                vinlist2 = [v['vin'] for v in vehicle_list2]
                if vinlist:
                    vinlist = list(ele1 for ele1 in vinlist for ele2 in vinlist2 if ele1 == ele2)
                else:
                    vinlist = vinlist2
            #sold
            if comp_select == "greaterthan":
                cursor.execute("""
                                        SELECT *
                                        FROM vehicle
                                        WHERE invoice_price*1.25 > % s
                                        AND sold_by <>\'\'
                                        """, (list_price,))
                vehicle_list_sold2 = cursor.fetchall()
                vinlist_sold2 = [v['vin'] for v in vehicle_list_sold2]
                if vinlist_sold:
                    vinlist_sold = list(ele1 for ele1 in vinlist_sold for ele2 in vinlist_sold2 if ele1 == ele2)
                else:
                    vinlist_sold = vinlist_sold2

            if comp_select == "lessthan":
                cursor.execute("""
                                        SELECT *
                                        FROM vehicle
                                        WHERE invoice_price*1.25 < % s
                                        AND sold_by <>\'\'
                                        """, (list_price,))
                vehicle_list_sold2 = cursor.fetchall()
                vinlist_sold2 = [v['vin'] for v in vehicle_list_sold2]
                if vinlist_sold:
                    vinlist_sold = list(ele1 for ele1 in vinlist_sold for ele2 in vinlist_sold2 if ele1 == ele2)
                else:
                    vinlist_sold = vinlist_sold2
            #all
            if comp_select == "greaterthan":
                cursor.execute("""
                                        SELECT *
                                        FROM vehicle
                                        WHERE invoice_price*1.25 > % s
                                        
                                        """, (list_price,))
                vehicle_list_all2 = cursor.fetchall()
                vinlist_all2 = [v['vin'] for v in vehicle_list_sold2]
                if vinlist:
                    vinlist_all = list(ele1 for ele1 in vinlist_all for ele2 in vinlist_all2 if ele1 == ele2)
                else:
                    vinlist_all = vinlist_all2

            if comp_select == "lessthan":
                cursor.execute("""
                                        SELECT *
                                        FROM vehicle
                                        WHERE invoice_price*1.25 < % s
                                        
                                        """, (list_price,))
                vehicle_list_all2 = cursor.fetchall()
                vinlist_all2 = [v['vin'] for v in vehicle_list_all2]
                if vinlist_all:
                    vinlist_all = list(ele1 for ele1 in vinlist_all for ele2 in vinlist_all2 if ele1 == ele2)
                else:
                    vinlist_all = vinlist_all2

        if vehicle_type != "":
             #unsold
            cursor.execute("""
                    with typeAdded as
                        (SELECT vin,
                            case
                                when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
                                when EXISTS(select * from convertible where convertible.vin=vehicle.vin) then 'convertible'
                                when EXISTS(select * from truck where truck.vin=vehicle.vin) then 'truck'
                                when EXISTS(select * from suv where suv.vin=vehicle.vin) then 'suv'
                                when EXISTS(select * from vanorminivan where vanorminivan.vin=vehicle.vin) then 'vanorminivan'
                                else \"\"
                        end as v_type,sold_by
                        FROM vehicle)
                    select *
                    from typeAdded
                    where v_type = %s
                    And sold_by=\'\'
                        """, (vehicle_type,))
            vehicle_list2 = cursor.fetchall()
            vinlist2 = [v['vin'] for v in vehicle_list2]

            if vinlist:
                vinlist = list(ele1 for ele1 in vinlist for ele2 in vinlist2 if ele1 == ele2)
            else:
                vinlist = vinlist2

             #sold
            cursor.execute("""
                    with typeAdded as
                        (SELECT vin,
                            case
                                when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
                                when EXISTS(select * from convertible where convertible.vin=vehicle.vin) then 'convertible'
                                when EXISTS(select * from truck where truck.vin=vehicle.vin) then 'truck'
                                when EXISTS(select * from suv where suv.vin=vehicle.vin) then 'suv'
                                when EXISTS(select * from vanorminivan where vanorminivan.vin=vehicle.vin) then 'vanorminivan'
                                else \"\"
                        end as v_type,sold_by
                        FROM vehicle)
                    select *
                    from typeAdded
                    where v_type = %s
                    And sold_by<>\'\'
                        """, (vehicle_type,))
            vehicle_list_sold2 = cursor.fetchall()
            vinlist_sold2 = [v['vin'] for v in vehicle_list_sold2]


            if vinlist_sold:
                vinlist_sold = list(ele1 for ele1 in vinlist_sold for ele2 in vinlist_sold2 if ele1 == ele2)
            else:
                vinlist_sold = vinlist_sold2

             #all
            cursor.execute("""
                    with typeAdded as
                        (SELECT vin,
                            case
                                when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
                                when EXISTS(select * from convertible where convertible.vin=vehicle.vin) then 'convertible'
                                when EXISTS(select * from truck where truck.vin=vehicle.vin) then 'truck'
                                when EXISTS(select * from suv where suv.vin=vehicle.vin) then 'suv'
                                when EXISTS(select * from vanorminivan where vanorminivan.vin=vehicle.vin) then 'vanorminivan'
                                else \"\"
                        end as v_type,sold_by
                        FROM vehicle)
                    select *
                    from typeAdded
                    where v_type = %s
                 
                        """, (vehicle_type,))
            vehicle_list_all2 = cursor.fetchall()
            vinlist_all2 = [v['vin'] for v in vehicle_list_all2]


            if vinlist_all:
                vinlist_all = list(ele1 for ele1 in vinlist_all for ele2 in vinlist_all2 if ele1 == ele2)
            else:
                vinlist_all = vinlist_all2


        if keyword != "":
             #unsold
            cursor.execute("""
                    select *
                    from vehicle v
                    inner join manufacturer m on v.vin = m.vin
                    where sold_by=\'\' and (description like %s or m.manufacturer_name like %s
                    or model_name like %s or model_year like %s)
                          """
                           , (
                           {'%' + keyword + '%'}, {'%' + keyword + '%'}, {'%' + keyword + '%'}, {'%' + keyword + '%'},))

            vehicle_list2 = cursor.fetchall()
            vinlist2 = [v['vin'] for v in vehicle_list2]
            # print("entered keyword")
            # print("keyword")
            # print(keyword)
            # print("list:")
            # print(vinlist)
            # print("list2:")
            # print(vinlist2)
            # print("left keyword")
            if vinlist:
                vinlist = list(ele1 for ele1 in vinlist for ele2 in vinlist2 if ele1 == ele2)
            else:
                vinlist = vinlist2
             #sold
            cursor.execute("""
                    select *
                    from vehicle v
                    inner join manufacturer m on v.vin = m.vin
                    where sold_by<>\'\' and (description like %s or m.manufacturer_name like %s
                    or model_name like %s or model_year like %s)
                          """
                           , (
                           {'%' + keyword + '%'}, {'%' + keyword + '%'}, {'%' + keyword + '%'}, {'%' + keyword + '%'},))

            vehicle_list_sold2 = cursor.fetchall()
            vinlist_sold2 = [v['vin'] for v in vehicle_list_sold2]
            # print("entered keyword")
            # print("keyword")
            # print(keyword)
            # print("list:")
            # print(vinlist)
            # print("list2:")
            # print(vinlist2)
            # print("left keyword")
            if vinlist_sold:
                vinlist_sold = list(ele1 for ele1 in vinlist_sold for ele2 in vinlist_sold2 if ele1 == ele2)
            else:
                vinlist_sold = vinlist_sold2
             #all
            cursor.execute("""
                    select *
                    from vehicle v
                    inner join manufacturer m on v.vin = m.vin
                    where description like %s or m.manufacturer_name like %s
                    or model_name like %s or model_year like %s
                          """
                           , (
                           {'%' + keyword + '%'}, {'%' + keyword + '%'}, {'%' + keyword + '%'}, {'%' + keyword + '%'},))

            vehicle_list_all2 = cursor.fetchall()
            vinlist_all2 = [v['vin'] for v in vehicle_list_all2]
            # print("entered keyword")
            # print("keyword")
            # print(keyword)
            # print("list:")
            # print(vinlist)
            # print("list2:")
            # print(vinlist2)
            # print("left keyword")
            if vinlist_all:
                vinlist_all = list(ele1 for ele1 in vinlist_all for ele2 in vinlist_all2 if ele1 == ele2)
            else:
                vinlist_all = vinlist_all2

        # print("finally vinlist:")
        sorted(vinlist)
        # print(vinlist)

        data = []
        count=0
        for item in list(vinlist):
            cursor.execute("""
            with typeAdded as
                (SELECT *, 
                case
                   when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
                   when EXISTS(select * from convertible where convertible.vin=vehicle.vin) then 'convertible'
                   when EXISTS(select * from truck where truck.vin=vehicle.vin) then 'truck'
                   when EXISTS(select * from suv where suv.vin=vehicle.vin) then 'suv'
                   when EXISTS(select * from vanorminivan where vanorminivan.vin=vehicle.vin) then 'vanorminivan'
                   else ""
                end as v_type
                FROM vehicle)
            select *
            from typeAdded v
            inner join color c on v.vin =c.vin
            inner join manufacturer m on v.vin=m.vin
            where v.vin=%s
            """, (item,))
            rst_one = cursor.fetchone()
            rst_one["list_price"] = round(rst_one["invoice_price"] * 1.25, 2)
            min_sold_price[item] = round(rst_one["invoice_price"] * 0.95, 2)
            data.append(rst_one)
            count+=1
        print("number of unsold car:" + str(count))



        data_sold= []
        count=0
        for item in list(vinlist_sold):
            cursor.execute("""
            with typeAdded as
                (SELECT *, 
                case
                   when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
                   when EXISTS(select * from convertible where convertible.vin=vehicle.vin) then 'convertible'
                   when EXISTS(select * from truck where truck.vin=vehicle.vin) then 'truck'
                   when EXISTS(select * from suv where suv.vin=vehicle.vin) then 'suv'
                   when EXISTS(select * from vanorminivan where vanorminivan.vin=vehicle.vin) then 'vanorminivan'
                   else ""
                end as v_type
                FROM vehicle)
            select *
            from typeAdded v
            inner join color c on v.vin =c.vin
            inner join manufacturer m on v.vin=m.vin
            where v.vin=%s
            """, (item,))
            rst_one = cursor.fetchone()
            rst_one["list_price"] = round(rst_one["invoice_price"] * 1.25, 2)
            min_sold_price[item] = round(rst_one["invoice_price"] * 0.95, 2)
            data_sold.append(rst_one)
            count+=1

        print("number of sold car:" + str(count))


        data_all = []
        count=0
        for item in list(vinlist_all):
            cursor.execute("""
            with typeAdded as
                (SELECT *, 
                case
                   when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
                   when EXISTS(select * from convertible where convertible.vin=vehicle.vin) then 'convertible'
                   when EXISTS(select * from truck where truck.vin=vehicle.vin) then 'truck'
                   when EXISTS(select * from suv where suv.vin=vehicle.vin) then 'suv'
                   when EXISTS(select * from vanorminivan where vanorminivan.vin=vehicle.vin) then 'vanorminivan'
                   else ""
                end as v_type
                FROM vehicle)
            select *
            from typeAdded v
            inner join color c on v.vin =c.vin
            inner join manufacturer m on v.vin=m.vin
            where v.vin=%s
            """, (item,))
            rst_one = cursor.fetchone()
            rst_one["list_price"] = round(rst_one["invoice_price"] * 1.25, 2)
            min_sold_price[item] = round(rst_one["invoice_price"] * 0.95, 2)
            data_all.append(rst_one)
            count+=1

        print("number of all car:" + str(count))
            # print(data)
            # print("my dictionary: ")
            # print(min_sold_price)

        #     cursor.execute("""
        #     select *, format((invoice_price * 1.25), 2) AS
        #     list_price, (case
        #                  when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
        #                  when EXISTS(select * from convertible where convertible.vin = vehicle.vin) then 'convertible'
        #                  when EXISTS(select * from truck where truck.vin = vehicle.vin) then 'truck'
        #                  when EXISTS(select * from suv where suv.vin = vehicle.vin) then 'suv'
        #                  when EXISTS(select * from vanorminivan where vanorminivan.vin = vehicle.vin) then 'vanorminivan'
        #                  else NULL
        #                  end) as type
        #     from vehicle
        #     left join color on vehicle.vin = color.vin
        #     left join manufacturer on vehicle.vin = manufacturer.vin
        #     WHERE vehicle.vin = % s
        #     AND sold_by IS NULL
        #     order by vehicle.vin ASC;
        #     """, (item,))

        #     resultdict = cursor.fetchone()
        #     data.append(resultdict)

        # print("data:", data)

        # cursor.execute("""
        # select *, format((invoice_price*1.25),2) AS list_price, (case
        #        when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
        #        when EXISTS(select * from convertible where convertible.vin=vehicle.vin) then 'convertible'
        #        when EXISTS(select * from truck where truck.vin=vehicle.vin) then 'truck'
        #        when EXISTS(select * from suv where suv.vin=vehicle.vin) then 'suv'
        #        when EXISTS(select * from vanorminivan where vanorminivan.vin=vehicle.vin) then 'vanorminivan'
        #        else NULL
        #       end) as type
        #     from vehicle
        #     left join color on vehicle.vin = color.vin
        #     left join manufacturer on vehicle.vin = manufacturer.vin
        #     where model_name= %s
        #     and model_year= %s
        #     and sold_by IS NOT NULL
        #     having type= %s
        #     and color= %s
        #     and manufacturer_name= %s
        #     and list_price<=%s  or list_price>%s
        #     # OR (
        #     #     manufacturer_name LIKE %s
        #     #     OR model_year LIKE %s
        #     #     OR model_name LIKE %s
        #     #     OR description LIKE %s
        #     #     )
        #     order by vehicle.vin ASC;
        # """, (model_name, model_year, vehicle_type, color, manufacturer_name, list_price, ))
        # data = cursor.fetchall()

        # num_unsold_vehicles=0
        # vehicle_list=[]
        # data=[]
        # print("leave advanced_search_inventory")
        sorted(data, key=lambda i: i['vin'])
        # print(data)

        return render_template('advanced_search_inventory.html',
                           # vehicle_list=vehicle_list,
                           user=user,
                           salespeople_list=salespeople_list,
                           owner_list=owner_list,
                           data=data,
                           data_all = data_all,
                           data_sold = data_sold,
                           inventoryclerk_list=inventoryclerk_list,
                           curr_date=curr_date,
                           min_sold_price=min_sold_price,
                           manager_list=manager_list
                           # msg=msg
                           )


##############################################################
## vehicle details with repair records and sale records  12/4
##############################################################
@app.route('/loggedin_home/inventory/advanced_search_inventory/vehicle_detail_repair_part/<string:rowData>', methods=['GET', 'POST'])
@login_required
def vehicle_detail_repair_part(rowData):
    ## get the current user and the authorized uses to perform functionality on editing and deleting
    user = session['username']

    manager_list = get_manager_list()  # can sell the vehicle
    owner_list = get_owner_list()

    if user not in manager_list:
        return render_template('444.html')

    today = date.today()
    curr_date = today.strftime("%Y-%m-%d")
    msg = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # get the sales records of the vehicle
    cursor.execute("""
        WITH customer as ( SELECT driver_id as cust_id, concat(first_name, ' ', last_name) as name, street_address,city,state,zip_code, phone_number,email
                      FROM individual 
                      UNION ALL 
                      SELECT tax_id as cust_id, business_name, street_address,city,state,zip_code, phone_number,email
                      FROM business)
                      SELECT s.purchase_date_time, 
                      v.invoice_price, 
                      round(v.invoice_price*1.25, 2) AS list_price, 
                      v.username as clerk, 
                      s.username as salesperson,
                      c.name,
                      v.username as clerk,
                      s.sold_price,
                      v.addition_date,
                      c.street_address,
                      c.city,
                      c.state,
                      c.zip_code,
                      c.phone_number,
                      c.email,
                      v.vin,
                      concat(user.first_name, ' ', user.last_name) as salespersonname
                      FROM vehicle v
                      JOIN salestransaction s on v.vin = s.vin 
                      JOIN customer c ON s.customer_id = c.cust_id 
                      JOIN user on user.username=s.username
                      where v.vin=%s
        """, (rowData,))
    sale_list = cursor.fetchall()

    # get repair records
    cursor.execute("""
    WITH customer as ( SELECT driver_id as cust_id, concat(first_name, ' ', last_name) as name
                  FROM individual 
                  UNION ALL 
                  SELECT tax_id as cust_id, business_name
                  FROM business)
    SELECT r.start_date, r.complete_date, r.vin, r.odometer, round(SUM(p.price*p.quantity), 2) as part_cost, 
    r.labor_charge, round(SUM(p.price*p.quantity)+r.labor_charge, 2) AS total_cost, user.first_name, 
    user.last_name, user.username as servicewriter, c.name,
    concat(user.first_name, ' ', user.last_name) as servicewritername
        FROM repair r JOIN part p ON ( r.start_date = p.start_date AND r.vin = p.vin)
        JOIN user on r.username=user.username
        JOIN customer c ON r.customer_id = c.cust_id 
        where r.vin=%s
        GROUP BY 1, 2, 3, 4, 6
        order by start_Date DESC, complete_date DESC
        """, (rowData,))
    repair_list = cursor.fetchall()

    return render_template('vehicle_detail_repair_part.html',
                           sale_list=sale_list,
                           repair_list=repair_list)




##########################
## add vehicle
##########################
@app.route('/loggedin_home/inventory/add_vehicle/', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    # print("enter add_vehicle")
    # print("user: " + session['username'])
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    ## get the current user
    user = session['username']
    # check if the user is inventoryclerk
    inventoryclerk_list = get_inventoryclerk_list()

    # get number of unsold vehicles
    num_unsold_vehicles = get_unsold_vechile_number()

    # get unsold vehicle list
    unsold_vehicle_list = get_unsold_vehicle_list()
    all_user_list = get_all_users_list()

    # 1. get the all the information of unsold vehicles (tested correct--77 vehicles)
    vehicle_list = get_unsold_vehicle_list()
    vinlist = {v['vin'] for v in vehicle_list}  # get all unsold vin list

    vehicle_type1, manufacturer_name1, model_name1, color1 = get_vehicle_attributes_public()
    salespeople_list = get_salesperson_list()  # can sell the vehicle
    owner_list = get_owner_list()
    today = date.today()
    curr_date = today.strftime("%Y-%m-%d")

    # get all vin list in the databse
    all_vin_list = get_all_vin_list()

    msg = ''

    # for item in (inventoryclerk_list + owner_list):
    #     print("user " + item)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # if request.method == 'POST' and (user in salespeople_list or user in owner_list):
    if request.method == 'POST' :
        # print("entered add_vehicle post method")
        vin = request.form.get('vin')  # anonymous user cannot use vin to search
        vehicle_type = request.form.get('vehicle_type')
        # print("vehicle_type " + vehicle_type)
        # if not vehicle_type:
        #     vehicle_type = None
        manufacturer_name = request.form.get('manufacturer_name')
        # print("manufacturer_name " + manufacturer_name)
        # if not manufacturer_name:
        #     manufacturer_name = None
        model_name = request.form.get('model_name')
        # print("model_name " + model_name)
        # if not model_name:
        #     model_name = None
        model_year = request.form.get('model_year')
        # print("model_year " + model_year)
        # if not model_year:
        #     model_year = None
        color = request.form.get('color')
        # print("color " + color)
        # if not color:
        #     color = None
        list_price = request.form.get('list_price')
        # print("list_price " + list_price)
        # if not list_price:
        #     list_price = None
        invoice_price = request.form.get('invoice_price')
        # print("invoice_price " + invoice_price)
        # if not invoice_price:
        #     invoice_price = None
        added_by = request.form.get('addedby')
        # print("added by " + added_by)
        # if not vehicle_type:
        #     vehicle_type = None
        # sold_by = request.form.get('soldby')
        # print("sold by " + sold_by)
        # if not sold_by:
        #     sold_by = None
        keyword = request.form.get('description')
        # print("keyword " + keyword)
        # if not keyword:
        #     keyword = None

        num_door = request.form.get('num_door')
        # print("num_door " + num_door)

        back_seat = request.form.get("back_seat")
        # print("back_seat " + back_seat)

        roof_type = request.form.get("roof_type")
        # print("roof_type " + roof_type)

        cargo_capacity = request.form.get("cargo_capacity")
        # print("cargo_capacity " + cargo_capacity)

        cover_type = request.form.get("cover_type")
        # print("cover_type " + cover_type)

        num_rearAxles = request.form.get("num_rearAxles")
        # print("num_rearAxles "+num_rearAxles)

        back_door = request.form.get("back_door")
        # print("back_door " + back_door)

        drivetrain_type = request.form.get("drivetrain_type")
        # print("drivetrain_type " + drivetrain_type)

        cupholders = request.form.get("cupholders")
        # print("cupholders " + cupholders)

        sold_by = ''

        cursor.execute("select * from vehicle where vin=%s;", (vin,))
        check_vin_exist=cursor.fetchone()
        if not check_vin_exist:
            print("vin can be used")


            cursor.execute("""
                    insert into vehicle
                    values (%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (vin, model_name, model_year, invoice_price, keyword, curr_date, added_by, sold_by,))

            cursor.execute("""
                insert into color
                values (%s,%s)
                """, (color, vin))
            cursor.execute("""
                insert into manufacturer
                values(%s,%s)
                """, (vin, manufacturer_name))

            if vehicle_type == "vanorminivan":
                cursor.execute("""
                    insert into vanorminivan
                    values(%s,%s)
                    """, (vin, back_door,)
                               )
            elif vehicle_type == "car":
                cursor.execute("""
                    insert into car
                    values(%s,%s)
                    """, (vin, num_door)
                               )
            elif vehicle_type == "convertible":
                cursor.execute("""
                    insert into convertible
                    values(%s,%s,%s)
                    """, (vin, roof_type, back_seat)
                               )
            elif vehicle_type == "suv":
                cursor.execute("""
                    insert into suv
                    values(%s,%s,%s)
                    """, (vin, drivetrain_type, cupholders)
                               )
            elif vehicle_type == "truck":
                cursor.execute("""
                    insert into truck
                    values(%s,%s,%s,%s)
                    """, (vin, cargo_capacity, cover_type, num_rearAxles)
                               )
            mysql.connection.commit()

            msg="added a vehicle successfully!"
            return render_template('add_vehicle_successful.html')
        else:
            msg="Alert! We have this VIN in our database! Please try another VIN"
    # print("leave add_vehicle")
    return render_template('add_vehicle.html',
                       msg=msg,
                       manufacturer_name=manufacturer_name1,
                       model_name=model_name1,
                       vehicle_type=vehicle_type1,
                       color=color1,
                       vehicle_list=vehicle_list,
                       num_unsold_vehicles=num_unsold_vehicles,
                       user=user,
                       inventoryclerk_list=inventoryclerk_list,
                       unsold_vehicle_list=unsold_vehicle_list,
                       owner_list=owner_list,
                       all_vin_list=all_vin_list
                       )



###########################
# update vehicle
###########################
@app.route('/loggedin_home/inventory/advanced_search_inventory/update', methods=['POST', 'GET'])
@login_required
def update():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        id_data = request.form['vin']
        vehicle_type = request.form['type']
        manufacturer_name = request.form['manufacturer_name']
        color = request.form['color']
        model_name = request.form['model_name']
        model_year = request.form['model_year']
        invoice_price = request.form['invoice_price']
        list_price = request.form['list_price']
        addition_date = request.form['addition_date']
        description = request.form['description']

        cursor.execute("""
               UPDATE vehicle
               SET model_name=%s, model_year=%s, invoice_price=%s,
                description=%s
               WHERE vin=%s
            """, (model_name, model_year, invoice_price,
                  description, id_data))
        mysql.connection.commit()

        cursor.execute("""
                       UPDATE color
                       SET color=%s
                       WHERE vin=%s
                    """, (color, id_data))
        mysql.connection.commit()
        flash("Data Updated Successfully")

        return redirect(url_for('advanced_search_inventory'))


############################################
## Customer page
############################################
@app.route('/loggedin_home/customer/', methods=['GET', 'POST'])
@login_required
def customer():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    user = session['username']  # display the current_user

    salespeople_list = get_salesperson_list()  # can sell the vehicle
    servicewriter_list = get_servicewriter_list()
    manager_list = get_manager_list()
    owner_list = get_owner_list()

    print("enter customer  ")
    msg = ''
    today = date.today()
    curr_date = today.strftime("%Y-%m-%d")

    list_individual = db_para.get_all_individuals()
    list_business = db_para.get_all_business()
    # if request.method == 'POST' and (user in salespeople_list or user in owner_list):
    if request.method == 'POST' :
        print("enter post")

        if request.form["btn"] == "sell":
            vin = request.form.get('vin')
            # print("vin" + vin)
            vehicle_type = request.form.get('v_type')
            # print("vehicle_type" + vehicle_type)
            manufacturer_name = request.form.get('manufacturer_name')
            # print("manufacturer_name" + manufacturer_name)
            model_name = request.form.get('model_name')
            # print("model_name " + model_name)
            model_year = request.form.get('model_year')
            # print("model_year " + model_year)
            color = request.form.get('color')
            # print("color " + color)
            list_price = request.form.get('list_price')
            # print("list_price " + list_price)
            invoice_price = request.form.get('invoice_price')
            # print("invoice_price" + invoice_price)
            sold_price = request.form.get('sold_price')
            # print("sold_price" + sold_price)
            sold_by = request.form.get('soldby')
            # print("sold_by " + sold_by)
            sold_date = request.form.get('sold_date')
            keyword = request.form.get('description')
            # print("keyword " + keyword)
            session['sold_price'] = sold_price
            session['vin'] = vin
            session['keyword'] = keyword
            session['sold_date'] = sold_date
            session['vehicle_type'] = vehicle_type
            session['manufacturer_name'] = manufacturer_name
            session['model_name'] = model_name
            session['model_year'] = model_year
            session['color'] = color
            session['list_price'] = list_price
            session['invoice_price'] = invoice_price
            session['sold_by'] = sold_by

        if request.form["btn"] == "submit":
            # print("enter customer form")
            session['tax_id'] = request.form.get("tax_id")
            tax_id = session['tax_id']
            # print("tax_id " + tax_id)
            session['driver_id'] = request.form.get("driver_id")
            driver_id = session['driver_id']
            # print("driver_id " + driver_id)

            if tax_id == '' and driver_id != '':
                print("enter driver_id")

                # cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                # cursor.execute("""SELECT * FROM individual
                #        WHERE driver_id = %s
                #        """, (driver_id,))
                # individual = cursor.fetchone()
                sold_date = session['sold_date']
                vin = session['vin']
                sold_price = session['sold_price']
                driver_id = session['driver_id']
                sold_by = session['sold_by']
                cursor.execute("""
                       insert into salestransaction
                       values(%s,%s,%s,%s,%s)
                       """, (sold_date, sold_price, vin, driver_id, sold_by)
                               )
                cursor.execute("""
                       update vehicle v
                       set sold_by = %s
                       where v.vin=%s
                    """, (sold_by, vin,))
                mysql.connection.commit()

                return render_template('sold_successful.html', user=user)


            elif tax_id != '' and driver_id == '':
                print("enter tax_id")

                # cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                # cursor.execute("""SELECT * FROM individual
                #        WHERE driver_id = %s
                #        """, (driver_id,))
                # individual = cursor.fetchone()
                sold_date = session['sold_date']
                vin = session['vin']
                sold_price = session['sold_price']
                tax_id = session['tax_id']
                sold_by = session['sold_by']
                cursor.execute("""
                       insert into salestransaction
                       values(%s,%s,%s,%s,%s)
                       """, (sold_date, sold_price, vin, tax_id, sold_by)
                               )
                cursor.execute("""
                       update vehicle v
                       set sold_by = %s
                       where v.vin=%s
                    """, (sold_by, vin,))
                mysql.connection.commit()
                return render_template('sold_successful.html')


            elif tax_id == '' and driver_id == '':
                pass


    # print("leave customer")
    return render_template('customer.html',
                           msg=msg,
                           list_individual=list_individual,
                           list_business=list_business,
                           user=user,
                           salespeople_list=salespeople_list,
                           servicewriter_list=servicewriter_list,
                           manager_list=manager_list
                           )


###########################
# add business
###########################
@app.route('/loggedin_home/customer/add_business', methods=['GET', 'POST'])
@login_required
def add_business():
    user = session['username']
    salespeople_list = get_salesperson_list()  # can sell the vehicle
    owner_list = get_owner_list()
    if request.method == 'POST' and (user in salespeople_list or user in owner_list):
        tax_id = request.form.get('tax_id')
        business_name = request.form.get('business_name')
        contact_title = request.form.get("primary_contact_title")
        contact_first_name = request.form.get("primary_contact_first_name")
        contact_last_name = request.form.get("primary_contact_last_name")

        street_address = request.form.get('street_address')
        city = request.form.get('city')
        state = request.form.get('state')
        zip_code = request.form.get('zip_code')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            insert into business
            values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (tax_id, business_name, contact_title, contact_first_name, contact_last_name, street_address, city, state,
              zip_code, phone_number, email))
        mysql.connection.commit()
    return render_template('add_successful.html')


###########################
# add individual
###########################
@app.route('/loggedin_home/customer/add_individual', methods=['GET', 'POST'])
@login_required
def add_individual():
    user = session['username']
    salespeople_list = get_salesperson_list()  # can sell the vehicle
    owner_list = get_owner_list()


    msg=""
    if request.method == 'POST' and (user in salespeople_list or user in owner_list):
        driver_id = request.form.get('driver_id')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        street_address = request.form.get('street_address')
        city = request.form.get('city')
        state = request.form.get('state')
        zip_code = request.form.get('zip_code')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # check if the current id is in out database
        cursor.execute("select * from individual where driver_id=%s;", (driver_id,))
        check_id_exist = cursor.fetchone()

        if not check_id_exist:
            cursor.execute("""
                insert into individual
                values(%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (driver_id, first_name, last_name, street_address, city, state, zip_code, phone_number, email))
            mysql.connection.commit()
        else:
            msg="The ID you entered is already exist in our system! Please try again!"
    return render_template('add_successful.html', msg=msg)


###########################
# add customer
###########################
@app.route('/loggedin_home/customer/insert', methods=['GET', 'POST'])
@login_required
def insert_customer():
    # check if user exists in database
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    current_user = session['username']
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        driver_id = request.form['driver_id']
        street_address = request.form['street_address']
        city = request.form['city']
        state = request.form['state']
        zip_code = request.form['zip_code']
        email = request.form['email']

        # first insert the record into customer table
        cursor.execute("INSERT INTO customer (street_address, city, state, zip_code, email, username) "
                       "VALUES (%s, %s, %s, %s, %s, %s)",
                       (street_address, city, state, zip_code, email, current_user))
        # select the customer_id and insert the individual cols into individual table
        customer_id = cursor.execute("""
                       SELECT customer_id FROM customer
                       WHERE street_address = %s, city= %s, state= %s, zip_code= %s, email= %s
                       """, (street_address, city, state, zip_code, email))
        cursor.execute("INSERT INTO individual (customer_id, first_name, last_name, driver_id) "
                       "VALUES (%s, %s, %s, %s)",
                       (customer_id, first_name, last_name, driver_id))
        mysql.connection.commit()
        flash('Added successfully')
        cursor.close()
        # return jsonify('success')
        return redirect(url_for('customer'))


@app.route('/loggedin_home/customer/select', methods=['GET', 'POST'])
@login_required
def select_customer():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        print(customer_id)
        cursor.execute('SELECT * FROM customer c JOIN business b ON c.customer_id = b.customer_id'
                       'WHERE c.customer_id = %s', customer_id)
        individual_customers = cursor.fetchall()
        individual_customers_array = []
        for individual_customer in individual_customers:
            individual_customers_array_dict = {
                'Customer ID': individual_customer['customer_id'],
                'First Name': individual_customer['first_name'],
                'Last Name': individual_customer['last_name'],
                'Driver Licence': individual_customer['driver_id'],
                'Stress Address': individual_customer['street_address'],
                'City': individual_customer['city'],
                'State': individual_customer['state'],
                'Zip Code': individual_customer['zip_code'],
                'Phone Number': individual_customer['phone_number'],
                'Email': individual_customer['email']}
            individual_customers_array.append(individual_customers_array_dict)
            return json.dumps(individual_customers_array)
        # return json.dumps(individual_customers_array)


############################################
## Repair page
############################################
# modify starts from here 11-27
@app.route('/loggedin_home/repair/')
@login_required
def repair():
    # check if the user is servicewriter
    user = session['username']
    servicewriter_list = get_servicewriter_list()
    print("servicewriter_list", servicewriter_list)
    sold_vehicle_list = get_sold_vehicle_list()

    # if the user is not servicewriter return to error page
    if user not in servicewriter_list:
        return render_template('444.html')

    return render_template('repair.html',
                           user=user,
                           servicewriter_list=servicewriter_list,
                           sold_vehicle_list=sold_vehicle_list)




@app.route('/loggedin_home/repair/repair_search_result', methods=['GET', 'POST'])
@login_required
def repair_search_result():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # check if the user is servicewriter
    user = session['username']

    servicewriter_list = get_servicewriter_list()
    sold_vehicle_list = get_sold_vehicle_list()

    cursor.execute("""
        SELECT driver_id AS customer_id      
        FROM  individual
        UNION
        SELECT tax_id AS customer_id
        FROM   business
        """)
    customer_id_list = cursor.fetchall()

    today = date.today()
    curr_date = today.strftime("%Y-%m-%d")

    if request.method == 'POST':
        vin = request.form.get('vin')

        # 0. get number of repairs for the unsold vehecles who has repair records
        cursor.execute("""
                        SELECT COUNT(start_date)AS num_repairs
                        FROM repair
                        WHERE vin=%s;
                        """, (vin,))
        num_repairs = cursor.fetchone()

        # 1. get the sold_vechile_basic_details (single result for the searching sold vehicles)
        cursor.execute("""
        select DISTINCT(vehicle.vin),manufacturer.manufacturer_name, color.color, model_name, model_year, invoice_price, addition_date, vehicle.description, format((invoice_price*1.25),2) AS list_price, (case
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
            left join repair on vehicle.vin = repair.vin
            where sold_by !="" AND vehicle.vin = %s;
        """, (vin,))
        sold_vehicle_basic_info = cursor.fetchall()

        # 2. get the sold vehicles repair records which have repairs in the past
        cursor.execute("""
            SELECT * FROM repair WHERE start_date is not null and vin=%s;
                """, (vin,))
        sold_vehicle_repair_list = cursor.fetchall()


        # get the max odemeter if the vehicle have repair history

        cursor.execute("""
                SELECT odometer  FROM repair WHERE vin=%s
                """, (vin,))
        if_odometer = cursor.fetchone()


        cursor.execute("""
        SELECT max(odometer) as max_odometer FROM repair WHERE vin=%s
        """, (vin,))
        max_odometer = cursor.fetchone()

        # 3. get sold_vehicle if it doesn't have a repair record --return empty value
        cursor.execute("""
        select vehicle.vin,manufacturer.manufacturer_name, color.color, model_name, model_year, invoice_price, addition_date, format((invoice_price*1.25),2) AS list_price, (case
               when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
               when EXISTS(select * from convertible where convertible.vin=vehicle.vin) then 'convertible'
               when EXISTS(select * from truck where truck.vin=vehicle.vin) then 'truck'
               when EXISTS(select * from suv where suv.vin=vehicle.vin) then 'suv'
               when EXISTS(select * from vanorminivan where vanorminivan.vin=vehicle.vin) then 'vanorminivan'
               else NULL
              end) as type, repair.start_date, repair.complete_date, repair.odometer, repair.labor_charge, repair.description, repair.customer_id, repair.username
            from vehicle
            left join color on vehicle.vin = color.vin
            left join manufacturer on vehicle.vin = manufacturer.vin
            left join repair on vehicle.vin = repair.vin
            where sold_by !="" AND repair.start_date IS NOT NULL AND vehicle.vin= %s;
        """, (vin,))
        sold_vehicle_no_repair_list = cursor.fetchall()

        # 4. check if it is an unfinished repair --the update button can be seen
        '''
        SELECT * FROM `repair` WHERE complete_date is null and vin=%s;
        SELECT * FROM repair WHERE start_date is not null and complete_date is null and vin
        '''
        cursor.execute("""
                        SELECT IFNULL(complete_date, 1) null_check FROM `repair` WHERE complete_date is null and vin=%s
                        """, (vin,))
        sold_vehicle_unfinished_repair_list = cursor.fetchall()

        # 5. check if we can add new repair for the current vehicle
        cursor.execute("""
            select * 
            from vehicle v 
            left join repair r on v.vin=r.vin 
            where v.sold_by is not null and r.start_date is not null and r.complete_date is not null or r.vin is NULL
            having v.vin=%s;
                                """, (vin,))
        sold_vehicle_add_repair_list = cursor.fetchall()

        # cursor.execute('SELECT CURDATE() AS DATE;')
        # start_date = cursor.fetchone()


        msg = ''
        if not sold_vehicle_repair_list:
            msg = 'no records for this vehicle'

        return render_template("repair_search_result.html",
                               user=user,
                               sold_vehicle_list=sold_vehicle_list,
                               servicewriter_list=servicewriter_list,
                               sold_vehicle_basic_info=sold_vehicle_basic_info,
                               sold_vehicle_repair_list=sold_vehicle_repair_list,
                               # start_date=start_date,
                               sold_vehicle_no_repair_list=sold_vehicle_no_repair_list,
                               num_repairs=num_repairs,
                               sold_vehicle_unfinished_repair_list=sold_vehicle_unfinished_repair_list,
                               sold_vehicle_add_repair_list=sold_vehicle_add_repair_list,
                               if_odometer=if_odometer,
                               max_odometer=max_odometer,
                               customer_id_list=customer_id_list,
                               curr_date=curr_date
                               )



@app.route('/loggedin_home/repair/repair_search_result/repair_search_parts_result/<string:rowdata>/<string:rowdate>', methods=['GET'])
@login_required
def repair_search_parts_result(rowdata,rowdate):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # check if the user is servicewriter
    user = session['username']
    servicewriter_list = get_servicewriter_list()


    # get the sold vehicles repair records with parts added in the current record
    cursor.execute("""
        select * 
        from part
        join repair r on r.vin=part.vin and r.start_date=part.start_date
        where part.vin=%s and part.start_date=%s
        order by r.complete_date DESC
            """, (rowdata,rowdate))
    sold_vehicle_repair_parts_record = cursor.fetchall()



    return render_template("repair_search_parts_result.html",
                           user=user,
                           servicewriter_list=servicewriter_list,
                           sold_vehicle_repair_parts_record=sold_vehicle_repair_parts_record
                           )

@app.route('/loggedin_home/repair/repair_search_result/add_repair', methods=['GET', 'POST'])
@login_required
def add_repair():
    # current username will be stored as the service writer
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    current_user = session['username']

    today = date.today()
    curr_date = today.strftime("%Y-%m-%d")

    # get the customer id list
    cursor.execute("""
    SELECT driver_id AS customer_id      
    FROM  individual
    UNION
    SELECT tax_id AS customer_id
    FROM   business
    """)
    customer_id_list=cursor.fetchall()

    if request.method == "POST":
        flash("Data Inserted Successfully")

        vin = request.form['vin']
        start_date = request.form['start_date']
        odometer = request.form['odometer']
        labor_charge = request.form['labor_charge']
        description = request.form['description']
        customer_id = request.form['customer_id']
        servicewriter = request.form['username']

        part_number = request.form['part_number']
        price = request.form['price']
        vendor_name = request.form['vendor_name']
        quantity = request.form['quantity']

        # the start date will be the current date
        # cursor.execute('SELECT CURDATE() AS DATE;')
        # start_date = cursor.fetchone()
        # start_date = start_date['DATE']

        # when update, the current date is the complete date
        cursor.execute('SELECT CURDATE() AS DATE;')
        complete_date = cursor.fetchone()

        cursor.execute("""
        INSERT INTO repair
        (start_date, odometer, labor_charge,
        description, username, vin, customer_id)
        VALUES (%s,  %s, %s, %s,  %s, %s, %s)
        """, (start_date, odometer, labor_charge, description, servicewriter, vin, customer_id))
        mysql.connection.commit()

        # insert parts
        cursor.execute("""
                           INSERT INTO part (vin, start_date, part_number, price, vendor_name, quantity)
                           VALUES (%s, %s, %s, %s, %s, %s)
                        """, (vin, start_date, part_number, price, vendor_name, quantity,))

        mysql.connection.commit()

        # get the current vehicle whole repair history after adding new repair
        cursor.execute("""
                        select *
                        from repair
                        where start_date=%s and odometer=%s and labor_charge=%s and 
                        description=%s and username=%s and vin=%s and customer_id=%s 

                        ;
                            """, (start_date, odometer,
                                  labor_charge, description,
                                  servicewriter, vin, customer_id,
                                  ))

        repair_records_after_adding = cursor.fetchall()

        return render_template("add_repair.html",
                               # start_date=start_date,
                               current_user=current_user,
                               customer_id_list=customer_id_list,
                               repair_records_after_adding=repair_records_after_adding,
                               curr_date=curr_date
                               )



# @app.route('/loggedin_home/repair/repair_search_result/repair_update/<string:>/<string:rowData>', methods=['POST', 'GET'])
# @login_required
# def repair_update(rowvin, rowData):
#     # current username will be stored as the service writer
#     current_user = session['username']
#     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#
#     today = date.today()
#     curr_date = today.strftime("%Y-%m-%d")
#
#
#     vin = request.form['vin']
#     labor_charge = request.form['labor_charge']
#     start_date = request.form['start_date']
#     # complete_date = request.form['complete_date']
#
#     part_number = request.form['part_number']
#     price = request.form['price']
#     vendor_name = request.form['vendor_name']
#     quantity = request.form['quantity']
#
#     # Update labor_charge
#     if labor_charge:
#         cursor.execute("""
#                UPDATE repair
#                SET labor_charge=%s
#                WHERE vin=%s
#             """, (labor_charge, vin,))
#         mysql.connection.commit()
#
#     ## add new parts
#     if part_number:
#         cursor.execute("""
#                INSERT INTO part (vin, start_date, part_number, price, vendor_name, quantity)
#                VALUES (%s, %s, %s, %s, %s, %s)
#             """, (vin, start_date, part_number, price, vendor_name, quantity,))
#         mysql.connection.commit()
#
#
#
#     # when update, the current date is the complete date
#     cursor.execute('SELECT CURDATE() AS DATE;')
#     current_date = cursor.fetchone()
#
#     return render_template("repair_update.html",
#                            current_date=current_date,
#                            current_user=current_user,
#                            curr_date=curr_date
#                            )


@app.route('/loggedin_home/repair/repair_search_result/update_repair', methods=['POST', 'GET'])
@login_required
def update_repair():
    # current username will be stored as the service writer
    current_user = session['username']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    today = date.today()
    curr_date = today.strftime("%Y-%m-%d")

    if request.method == 'POST':
        flash("Data Updated Successfully")

        vin = request.form['vin']
        labor_charge = request.form['labor_charge']
        start_date = request.form['start_date']

        print("start_date0000000000", start_date)
        # complete_date = request.form['complete_date']

        part_number = request.form['part_number']
        price = request.form['price']
        vendor_name = request.form['vendor_name']
        quantity = request.form['quantity']

        # Update labor_charge
        if labor_charge:
            cursor.execute("""
                   UPDATE repair
                   SET labor_charge=%s
                   WHERE vin=%s and start_date=%s
                """, (labor_charge, vin, start_date))
            mysql.connection.commit()

        ## add new parts
        if part_number:
            cursor.execute("""
                   INSERT INTO part (vin, start_date, part_number, price, vendor_name, quantity)
                   VALUES (%s, %s, %s, %s, %s, %s)
                """, (vin, start_date, part_number, price, vendor_name, quantity,))
            mysql.connection.commit()



        # when update, the current date is the complete date
        cursor.execute('SELECT CURDATE() AS DATE;')
        current_date = cursor.fetchone()

        return render_template("update_repair.html",
                               current_date=current_date,
                               current_user=current_user,
                               curr_date=curr_date
                               )


@app.route('/loggedin_home/repair/repair_search_result/complete_repair', methods=['POST', 'GET'])
@login_required
def complete_repair():
    # current username will be stored as the service writer
    current_user = session['username']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        flash("Repair Completion Successfully")
        vin = request.form['vin']
        complete_date = request.form['complete_date']
        start_date = request.form['start_date']

        cursor.execute("""
        UPDATE repair
        SET complete_date=%s
        WHERE vin=%s
        """, (complete_date, vin,))
        mysql.connection.commit()

        # # get the current vehicle whole repair history after updating
        # cursor.execute("""
        #                 select vehicle.vin,
        #                 manufacturer.manufacturer_name,
        #                 color.color, model_name, model_year,
        #                 invoice_price, addition_date,
        #                 format((invoice_price*1.25),2) AS list_price,
        #                 (case
        #                    when EXISTS(select * from car where car.vin=vehicle.vin) then 'car'
        #                    when EXISTS(select * from convertible where convertible.vin=vehicle.vin) then 'convertible'
        #                    when EXISTS(select * from truck where truck.vin=vehicle.vin) then 'truck'
        #                    when EXISTS(select * from suv where suv.vin=vehicle.vin) then 'suv'
        #                    when EXISTS(select * from vanorminivan where vanorminivan.vin=vehicle.vin) then 'vanorminivan'
        #                    else NULL
        #                   end) as type, repair.start_date, repair.complete_date, repair.odometer, repair.labor_charge,
        #                   repair.description, repair.customer_id, repair.username,
        #                   part.part_number, part.price, part.quantity, part.vendor_name
        #                 from vehicle
        #                 left join color on vehicle.vin = color.vin
        #                 left join manufacturer on vehicle.vin = manufacturer.vin
        #                 left join repair on vehicle.vin = repair.vin
        #                 left join part on vehicle.vin =part.vin
        #                 where sold_by !="" AND repair.start_date IS NOT NULL AND vehicle.vin= %s amd start_date=%s
        #                     """, (vin, start_date))
        # repair_records_after_updating = cursor.fetchall()
        # mysql.connection.commit()

        # when update, the current date is the complete date
        cursor.execute('SELECT CURDATE() AS DATE;')
        current_date = cursor.fetchone()

        return render_template("complete_repair.html",
                               # repair_records_after_updating=repair_records_after_updating,
                               current_date=current_date,
                               current_user=current_user,
                               # repair_records_after_updating=repair_records_after_updating
                               )

############################################
## Sales Orders page
############################################
@app.route('/loggedin_home/sales_orders/')
@login_required
def sales_orders():
    ## 1. check if the current user can view this page
    ## get the current username
    user = session['username']
    ## get the users who can view this page
    manager_list = get_manager_list()
    if user not in manager_list:
        return render_template('444.html')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
    SELECT * FROM salestransaction
    GROUP BY vin
    ORDER BY purchase_date_time DESC, sold_price DESC
    """)
    sales_orders = cursor.fetchall()

    return render_template("sales_orders.html",
                           user=user,
                           manager_list=manager_list, sales_orders=sales_orders)


############################################
## Report page
############################################
@app.route('/loggedin_home/report/')
@login_required
def report():
    ## 1. check if the current user can view this page
    ## get the current username
    user = session['username']
    ## get the users who can view this page
    manager_list = get_manager_list()
    if user not in manager_list:
        return render_template('444.html')
    return render_template("report.html",
                           user=user,
                           manager_list=manager_list)


########################
###  color_sales_report
########################
@app.route('/loggedin_home/report/color_sales_report/')
@login_required
def color_sales_report():
    ## check if the current user can view this page
    ## get the current username
    user = session['username']
    ## get the users who can view this page
    manager_list = get_manager_list()
    if user not in manager_list:
        return render_template('444.html')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    ## 30days
    cursor.execute("""
    SELECT
    CASE WHEN c.color LIKE '%,%' THEN 'Multiple' ELSE c.color END AS Color,
    COUNT(DISTINCT st.vin) as Vehicle_Sales_Count_30Days
    FROM
     SalesTransaction st JOIN Color c ON st.vin = c.vin
    WHERE
    datediff((SELECT MAX(purchase_date_time) as last_date
        FROM salestransaction), st.purchase_date_time) <= 30
    GROUP BY 1
    ORDER BY Color ASC;
    """)
    color_sales_30 = cursor.fetchall()

    ## 1year
    cursor.execute("""
    WITH last_sold as (
	SELECT MAX(purchase_date_time) as last_date
	FROM salestransaction)
    SELECT
    CASE WHEN c.color LIKE '%,%' THEN 'Multiple'
    ELSE c.color END AS Color
    , COUNT(DISTINCT st.vin) as Vehicle_Sales_Count_1year
    FROM
     SalesTransaction st JOIN Color c ON st.vin = c.vin, last_sold ls
    WHERE
     (YEAR(ls.last_date) - YEAR(st.purchase_date_time)) = 1
    GROUP BY 1
    ORDER BY Color ASC;
    """)
    color_sales_year = cursor.fetchall()

    ## all data
    cursor.execute("""
        SELECT
            CASE WHEN c.color LIKE '%,%' THEN 'Multiple'
            ELSE c.color END AS Color, COUNT(DISTINCT st.vin) as Vehicle_Sales_Count
            FROM
             SalesTransaction st JOIN Color c ON st.vin = c.vin
            GROUP BY 1
            ORDER BY Color ASC;
        """)
    color_sales_all = cursor.fetchall()

    return render_template("color_sales_report.html",
                           user=user,
                           manager_list=manager_list,
                           color_sales_30=color_sales_30,
                           color_sales_year=color_sales_year,
                           color_sales_all=color_sales_all
                           )


########################
###  type_sales_report
########################
@app.route('/loggedin_home/report/type_sales_report/')
@login_required
def type_sales_report():
    ## check if the current user can view this page
    ## get the current username
    user = session['username']
    ## get the users who can view this page
    manager_list = get_manager_list()
    if user not in manager_list:
        return render_template('444.html')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    ## 30days
    cursor.execute("""
        WITH
            VehicleType_temp AS (
             SELECT vin, 'Car' as Type FROM Car
             UNION
             SELECT VIN, 'Convertible' as Type FROM Convertible
             UNION
             SELECT VIN, 'Truck' as Type FROM Truck
             UNION
             SELECT VIN, 'SUV' as Type FROM SUV
             UNION
             SELECT VIN, 'VanOrMinivan' as Type FROM VanOrMinivan)

            SELECT vt.type, COUNT(DISTINCT vt.vin) as Vehicle_Sales_Count_Last_30Days
            FROM
             VehicleType_temp vt JOIN SalesTransaction st ON vt.vin = st.vin
            WHERE
             datediff((SELECT MAX(purchase_date_time) as last_date
                FROM salestransaction), st.purchase_date_time) <= 30
            GROUP BY vt.type
            ORDER BY vt.type;
        """)
    type_sales_30 = cursor.fetchall()

    ## 1year
    cursor.execute("""
            WITH last_sold as (
	SELECT MAX(purchase_date_time) as last_date
	FROM salestransaction
)
,
VehicleType_temp AS (
 SELECT vin, 'Car' as Type FROM Car
 UNION
 SELECT VIN, 'Convertible' as Type FROM Convertible
 UNION
 SELECT VIN, 'Truck' as Type FROM Truck
 UNION
 SELECT VIN, 'SUV' as Type FROM SUV
 UNION
 SELECT VIN, 'VanOrMinivan' as Type FROM VanOrMinivan)

SELECT vt.type, COUNT(DISTINCT vt.vin) as Vehicle_Sales_Count_Last_year
FROM
 VehicleType_temp vt JOIN SalesTransaction st ON vt.vin = st.vin, last_sold ls
WHERE
 (YEAR(ls.last_date) - YEAR(st.purchase_date_time)) = 1
GROUP BY vt.type
ORDER BY vt.type;
            """)
    type_sales_year = cursor.fetchall()

    ## all
    cursor.execute("""
            SELECT vt.type, COUNT(DISTINCT vt.vin) as Vehicle_Sales_Count
FROM
 (SELECT vin, 'Car' as Type FROM Car
 UNION
 SELECT VIN, 'Convertible' as Type FROM Convertible
 UNION
 SELECT VIN, 'Truck' as Type FROM Truck
 UNION
 SELECT VIN, 'SUV' as Type FROM SUV
 UNION
 SELECT VIN, 'VanOrMinivan' as Type FROM VanOrMinivan) vt JOIN SalesTransaction st ON vt.vin = st.vin
GROUP BY vt.type;
            """)
    type_sales_all = cursor.fetchall()

    return render_template("type_sales_report.html",
                           user=user,
                           manager_list=manager_list,
                           type_sales_30=type_sales_30,
                           type_sales_year=type_sales_year,
                           type_sales_all=type_sales_all
                           )


########################
###  manufacturer_sales_report
########################
@app.route('/loggedin_home/report/manufacturer_sales_report/')
@login_required
def manufacturer_sales_report():
    ## check if the current user can view this page
    ## get the current username
    user = session['username']
    ## get the users who can view this page
    manager_list = get_manager_list()
    if user not in manager_list:
        return render_template('444.html')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    ## 30days
    cursor.execute("""
SELECT m.manufacturer_name, count(DISTINCT st.vin) as vehicle_sold
FROM SalesTransaction st JOIN Manufacturer m ON st.vin = m.vin
WHERE datediff((SELECT MAX(purchase_date_time) as last_date
	FROM salestransaction), st.purchase_date_time) <= 30
GROUP BY 1
ORDER BY m.manufacturer_name;
            """)
    sales_30 = cursor.fetchall()

    ## 1year
    cursor.execute("""
                WITH last_sold as (
	SELECT MAX(purchase_date_time) as last_date
	FROM salestransaction
)
SELECT m.manufacturer_name, count(DISTINCT st.vin) as vehicle_sold
FROM SalesTransaction st JOIN Manufacturer m ON st.vin = m.vin, last_sold ls
WHERE (YEAR(ls.last_date) - YEAR(st.purchase_date_time)) = 1
GROUP BY 1
ORDER BY m.manufacturer_name;
                """)
    sales_year = cursor.fetchall()

    ## all
    cursor.execute("""
SELECT m.manufacturer_name, count(DISTINCT st.vin) as vehicle_sold
FROM SalesTransaction st JOIN Manufacturer m ON st.vin = m.vin
GROUP BY 1
ORDER BY m.manufacturer_name;
                """)
    sales_all = cursor.fetchall()

    return render_template("manufacturer_sales_report.html",
                           user=user,
                           manager_list=manager_list,
                           sales_all=sales_all,
                           sales_year=sales_year,
                           sales_30=sales_30)


########################
###  parts statistics
########################

@app.route('/loggedin_home/report/parts_stats_report/')
@login_required
def parts_stats_report():
    ## check if the current user can view this page
    ## get the current username
    user = session['username']
    ## get the users who can view this page
    manager_list = get_manager_list()
    if user not in manager_list:
        return render_template('444.html')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
    SELECT vendor_name, SUM(quantity) as number_of_part, ROUND(SUM(price*quantity), 2) as total_cost
    FROM part
    GROUP BY 1
    ORDER BY 3 DESC
    """)

    parts_sales = cursor.fetchall()

    return render_template("parts_stats_report.html",
                           user=user,
                           manager_list=manager_list,
                           parts_sales=parts_sales)


########################
###  avg_time_inventory_report
########################
@app.route('/loggedin_home/report/avg_time_inventory_report/')
@login_required
def avg_time_inventory_report():
    ## check if the current user can view this page
    ## get the current username
    user = session['username']
    ## get the users who can view this page
    manager_list = get_manager_list()
    if user not in manager_list:
        return render_template('444.html')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
 #    WITH VehicleType_temp AS (
 # SELECT vin, 'Car' as Type FROM Car
 # UNION
 # SELECT VIN, 'Convertible' as Type FROM Convertible
 # UNION
 # SELECT VIN, 'Truck' as Type FROM Truck
 # UNION
 # SELECT VIN, 'SUV' as Type FROM SUV
 # UNION
 # SELECT VIN, 'VanOrMinivan' as Type FROM VanOrMinivan)
 #
 # SELECT vt.vin, vt.type,
 # CASE WHEN datediff(st.purchase_date_time, v.addition_date) = '0' THEN 'N/A' ELSE datediff(st.purchase_date_time, v.addition_date) END AS Avg_in_inventory
 # FROM vehicletype_temp vt JOIN salestransaction st on vt.vin = st.vin JOIN vehicle v on vt.vin = v.vin
 # GROUP BY vt.vin
 # ORDER BY vt.type ASC, Avg_in_inventory DESC
 WITH VehicleType_temp AS (
 SELECT vin, 'Car' as Type FROM Car
 UNION
 SELECT VIN, 'Convertible' as Type FROM Convertible
 UNION
 SELECT VIN, 'Truck' as Type FROM Truck
 UNION
 SELECT VIN, 'SUV' as Type FROM SUV
 UNION
 SELECT VIN, 'VanOrMinivan' as Type FROM VanOrMinivan)

 SELECT vt.type, round(AVG(datediff(st.purchase_date_time, v.addition_date)),2) as Avg_in_inventory
 FROM vehicletype_temp vt JOIN salestransaction st on vt.vin = st.vin JOIN vehicle v on vt.vin = v.vin
 GROUP BY 1

    """)
    avg_time_inventory = cursor.fetchall()

    return render_template("avg_time_inventory_report.html",
                           user=user,
                           manager_list=manager_list,
                           avg_time_inventory=avg_time_inventory)


########################
###  Blow cost
########################
@app.route('/loggedin_home/report/below_cost_report/')
@login_required
def below_cost_report():
    ## check if the current user can view this page
    ## get the current username
    user = session['username']
    ## get the users who can view this page
    manager_list = get_manager_list()
    if user not in manager_list:
        return render_template('444.html')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
    WITH customer as (
SELECT driver_id as cust_id, concat(first_name, ' ', last_name) as name
FROM individual
UNION ALL
SELECT tax_id as cust_id, business_name
FROM business)

SELECT v.vin, st.purchase_date_time, v.invoice_price, st.sold_price, FORMAT(st.sold_price/v.invoice_price*100,2) as ratio, c.name as customer_name, st.username as sales_person
FROM vehicle v JOIN salestransaction st on v.vin = st.vin  JOIN customer c ON st.customer_id = c.cust_id
WHERE v.invoice_price > st.sold_price
GROUP BY v.vin
ORDER BY st.purchase_date_time DESC, ratio DESC;
    """)
    below_cost = cursor.fetchall()

    return render_template("below_cost_report.html",
                           user=user,
                           manager_list=manager_list,
                           below_cost=below_cost)


########################
###  Repair report
########################
@app.route('/loggedin_home/report/repair_report/')
@login_required
def repair_report():
    ## check if the current user can view this page
    ## get the current username
    user = session['username']
    ## get the users who can view this page
    manager_list = get_manager_list()
    if user not in manager_list:
        return render_template('444.html')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
    with repair_cost as (
    -- labor and parts
    SELECT r.start_date, r.vin, r.labor_charge, p.total_parts
    FROM repair r JOIN
        -- parts per order
        (SELECT vin, start_date, sum(price * quantity) as total_parts
        FROM part
        GROUP BY 1,2) p
        ON (r.vin = p.vin and r.start_date = p.start_date)),

    VehicleType_temp AS (
     SELECT vin, 'Car' as Type FROM Car
     UNION
     SELECT VIN, 'Convertible' as Type FROM Convertible
     UNION
     SELECT VIN, 'Truck' as Type FROM Truck
     UNION
     SELECT VIN, 'SUV' as Type FROM SUV
     UNION
     SELECT VIN, 'VanOrMinivan' as Type FROM VanOrMinivan)

    SELECT vt.type, COUNT(*) as total_repair, round(SUM(rc.labor_charge),2) as total_labor, round(SUM(rc.total_parts),2) as total_parts, round(SUM(rc.labor_charge)+SUM(rc.total_parts),2) as total, m.manufacturer_name
    FROM manufacturer m, vehicletype_temp vt, repair_cost rc
    WHERE m.vin = vt.vin and vt.vin = rc.vin
    GROUP BY manufacturer_name
    ORDER BY manufacturer_name, total_repair DESC;
    """)
    repair_manufacturer_list = cursor.fetchall()

    return render_template("repair_report.html",
                           user=user,
                           manager_list=manager_list,
                           repair_manufacturer_list=repair_manufacturer_list)


@app.route('/loggedin_home/report/repair_report/repair_type_report/<string:rowData>', methods=['GET'])
@login_required
def repair_type_report(rowData):
    ## check if the current user can view this page
    ## get the current username
    user = session['username']
    ## get the users who can view this page
    manager_list = get_manager_list()
    if user not in manager_list:
        return render_template('444.html')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""
    with repair_cost as (
    -- labor and parts
    SELECT r.start_date, r.vin, r.labor_charge, p.total_parts
    FROM repair r JOIN
        -- parts per order
        (SELECT vin, start_date, sum(price * quantity) as total_parts
        FROM part
        GROUP BY 1,2) p
        ON (r.vin = p.vin and r.start_date = p.start_date)),

    VehicleType_temp AS (
     SELECT vin, 'Car' as Type FROM Car
     UNION
     SELECT VIN, 'Convertible' as Type FROM Convertible
     UNION
     SELECT VIN, 'Truck' as Type FROM Truck
     UNION
     SELECT VIN, 'SUV' as Type FROM SUV
     UNION
     SELECT VIN, 'VanOrMinivan' as Type FROM VanOrMinivan)

    SELECT vt.type, COUNT(*) as total_repair, round(SUM(rc.labor_charge),2) as total_labor, round(SUM(rc.total_parts),2) as total_parts, round(SUM(rc.labor_charge)+SUM(rc.total_parts),2) as total, m.manufacturer_name
    FROM manufacturer m, vehicletype_temp vt, repair_cost rc
    WHERE m.vin = vt.vin and vt.vin = rc.vin and manufacturer_name=%s
    GROUP BY type
    ORDER BY type, total_repair DESC;
    """, (rowData,))
    repair_type_list = cursor.fetchall()
    return render_template("repair_type_report.html",
                           user=user,
                           manager_list=manager_list,
                           repair_type_list=repair_type_list)


@app.route('/loggedin_home/report/repair_report/repair_model_report/<string:rowData>/<string:rowtype>', methods=['GET'])
@login_required
def repair_model_report(rowData, rowtype):
    ## check if the current user can view this page
    ## get the current username
    user = session['username']
    ## get the users who can view this page
    manager_list = get_manager_list()
    if user not in manager_list:
        return render_template('444.html')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""
        with repair_cost as (
        -- labor and parts
        SELECT r.start_date, r.vin, r.labor_charge, p.total_parts
        FROM repair r JOIN
            -- parts per order
            (SELECT vin, start_date, sum(price * quantity) as total_parts
            FROM part
            GROUP BY 1,2) p
            ON (r.vin = p.vin and r.start_date = p.start_date)),

    VehicleType_temp AS (
     SELECT vin, 'Car' as Type FROM Car
     UNION
     SELECT VIN, 'Convertible' as Type FROM Convertible
     UNION
     SELECT VIN, 'Truck' as Type FROM Truck
     UNION
     SELECT VIN, 'SUV' as Type FROM SUV
     UNION
     SELECT VIN, 'VanOrMinivan' as Type FROM VanOrMinivan)

    SELECT v.model_name,vt.type, COUNT(*) as total_repair, round(SUM(rc.labor_charge),2) as total_labor, round(SUM(rc.total_parts),2) as total_parts, round(SUM(rc.labor_charge)+SUM(rc.total_parts),2) as total, manufacturer_name
    FROM manufacturer m, vehicletype_temp vt, repair_cost rc, vehicle v
    WHERE m.vin = vt.vin and vt.vin = rc.vin AND vt.vin = v.vin
    AND m.manufacturer_name = %s AND vt.type = %s
    GROUP BY 1, manufacturer_name
    ORDER BY 1, total_repair;
    """, (rowData, rowtype,))
    repair_model_list = cursor.fetchall()

    return render_template("repair_model_report.html",
                           user=user,
                           manager_list=manager_list,
                           repair_model_list=repair_model_list)


#############################
###  gross_customers_income
#############################

@app.route('/loggedin_home/report/gross_customers_income_report/')
@login_required
def gross_customers_income_report():
    ## check if the current user can view this page
    ## get the current username
    user = session['username']
    ## get the users who can view this page
    manager_list = get_manager_list()
    if user not in manager_list:
        return render_template('444.html')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
    with c as (
SELECT driver_id as customer_id, concat(first_name, ' ', last_name) as name
FROM individual
UNION
SELECT tax_id as customer_id, business_name as name
FROM business)
SELECT
bb.customer_id,
c.name,
FORMAT(sum(bb.amount),2) as Total_Spend

FROM
(
-- car sales amount
SELECT customer_id, sum(sold_price) as amount
FROM SalesTransaction
GROUP by 1
UNION ALL
-- repair total cost
SELECT  customer_id, SUM(labor_charge+ifnull(amount, 0)) as amount
FROM
(
SELECT r.start_date, r.vin, r.customer_id, r.labor_charge, (sum(p.price * p.quantity)) as amount
FROM Repair r LEFT JOIN part p on (r.vin = p.vin and r.start_date = p.start_date)
GROUP BY 1, 2, 3, 4) aa
GROUP by 1
) bb LEFT JOIN c ON bb.customer_id = c.customer_id
GROUP BY 1,2
ORDER BY sum(bb.amount) DESC
LIMIT 15
    """)
    gross_income_15 = cursor.fetchall()

    return render_template("gross_customers_income_report.html",
                           user=user,
                           manager_list=manager_list,
                           gross_income_15=gross_income_15)


@app.route('/loggedin_home/report/selected_customer_income_report/<string:rowdata>')
@login_required
def selected_customer_income_report(rowdata):
    ## check if the current user can view this page
    ## get the current username
    user = session['username']
    ## get the users who can view this page
    manager_list = get_manager_list()
    if user not in manager_list:
        return render_template('444.html')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # 1. sales records
    cursor.execute("""
    SELECT st.purchase_date_time as sale_date, st.sold_price, st.vin, v.model_year,  m.manufacturer_name,v.model_name, st.username as salesperson_name, user.first_name, user.last_name
    FROM salestransaction st JOIN vehicle v on st.vin = v.vin JOIN manufacturer m on st.vin = m.vin
    JOIN user on st.username=user.username
    WHERE st.customer_id = %s
    order by sale_date DESC, vin ASC
    """, (rowdata,))
    sales_records = cursor.fetchall()

    # 2. repair records
    cursor.execute("""
        SELECT r.start_date, r.complete_date, r.vin, r.odometer, round(SUM(p.price*p.quantity), 2) as part_cost, r.labor_charge, round(SUM(p.price*p.quantity)+r.labor_charge, 2) AS total_cost, user.first_name, user.last_name, user.username
        FROM repair r JOIN part p ON ( r.start_date = p.start_date AND r.vin = p.vin)
        JOIN user on r.username=user.username
        WHERE r.customer_id = %s
        GROUP BY 1, 2, 3, 4, 6
        order by start_Date DESC, complete_date DESC
        """, (rowdata,))
    repair_records = cursor.fetchall()

    return render_template("selected_customer_income_report.html",
                           user=user,
                           manager_list=manager_list,
                           sales_records=sales_records, repair_records=repair_records)


###################################################
## Sales Reports Monthly Yearly and Top Salesperson
###################################################

@app.route('/loggedin_home/report/month_year_sales_summary_report/')
@login_required
def month_year_sales_summary_report():
    ## check if the current user can view this page
    ## get the current username
    user = session['username']
    ## get the users who can view this page
    manager_list = get_manager_list()
    if user not in manager_list:
        return render_template('444.html')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
    SELECT year(st.purchase_date_time) as year,
    month(st.purchase_date_time) as month,
    COUNT(v.vin) as vehicle_sold,
    round(SUM(st.sold_price),2) AS total_income,
    round(SUM(st.sold_price - v.invoice_price),2) as net_income,
    round(SUM(st.sold_price)/sum(v.invoice_price),2)*100 as ratio
    FROM vehicle v JOIN salestransaction st on v.vin = st.vin
    GROUP BY 1, 2
    ORDER BY 1 DESC, 2 DESC
    """)
    month_year_sales_summary = cursor.fetchall()

    return render_template("month_year_sales_summary_report.html",
                           user=user,
                           manager_list=manager_list,
                           month_year_sales_summary=month_year_sales_summary)


@app.route('/loggedin_home/report/top_salesperson_report/<int:rowyear>/<int:rowmonth>', methods=['GET'])
@login_required
def top_salesperson_report(rowyear, rowmonth):
    ## check if the current user can view this page
    ## get the current username
    user = session['username']
    ## get the users who can view this page
    manager_list = get_manager_list()
    if user not in manager_list:
        return render_template('444.html')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
    SELECT st.username, u.first_name, u.last_name, count(vin) as vehicle_sold, round(sum(st.sold_price), 2) as total_sales
    FROM salestransaction st JOIN user u on st.username = u.username
    WHERE YEAR(st.purchase_date_time) = '%s' AND MONTH(st.purchase_date_time) = '%s'
    GROUP BY 1
    ORDER BY total_sales DESC, vehicle_sold DESC;
    """, (rowyear, rowmonth,))
    top_salesperson_sales_summary = cursor.fetchall()

    return render_template("top_salesperson_report.html",
                           user=user,
                           manager_list=manager_list,
                           top_salesperson_sales_summary=top_salesperson_sales_summary)


############################################
## Setting error page
############################################
@app.errorhandler(404)
def not_found(error=None):
    return render_template('404.html'), 404


############################################
## Setting logout
############################################
@app.route('/login/logout')
@login_required
def logout():
    # remove the session data--log out
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host='127.0.0.1', port=5002, debug=True)
