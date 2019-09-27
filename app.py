import psycopg2
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
import uuid
import datetime
from decimal import *
import pytz

from helpers import *

from time import gmtime,strftime
cur_time= strftime("%Y-%m-%d %H?",gmtime())

lim = 51
# House Amenties
def init_arr():
	temp_arr = {}
	temp_arr['near'] = '%'
	temp_arr['flat_no'] = '%'
	temp_arr['elevator'] = '%'
	temp_arr['Kitchen'] = '%'
	temp_arr['Living'] = '%'
	temp_arr['Flat_no'] = '%'
	temp_arr['bedroom'] = '%'
	temp_arr['price_min'] = 0
	temp_arr['price_max'] = 1000000
	temp_arr['district'] = (1,2,3,4,5,6,7,8,9,10,11,12,13)
	temp_arr['area_min'] = 0
	temp_arr['area_max'] = 1000
	temp_arr['buildingstructure'] = (0,1,2,3,4,5,6)
	return temp_arr


# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd
app.jinja_env.filters["lookup"] = lookup

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# connect to POSTGRES database
conn = psycopg2.connect(database="housing", user = "postgres", password = "@akanshu", host = "127.0.0.1", port = "5432")
conn.autocommit = True
# conn = sqlite3.connect('finance.db', check_same_thread=False)
db = conn.cursor()

db.execute('drop trigger if exists update_transaction on transaction_log')
db.execute('drop function if exists update_time')
db.execute('create or replace function update_time() returns trigger as $$begin update transaction_log set time = current_timestamp where transaction_id = new.transaction_id; return new; end; $$ language plpgsql')
db.execute('create trigger update_transaction after insert on transaction_log for each row execute procedure update_time()')
# db = SQL("sqlite?")

@app.route("/",methods=["GET", "POST"])
@login_required
def index():
	if request.method=="GET":
	    db.execute("select * from house_owner where id = %s union select * from tenant where id = %s limit 50",(session["user_id"],session["user_id"]))
	    trans = db.fetchall()
	    print (trans)
	    return render_template("index.html",trans=trans)
	else:
	    if 'remove' in request.form:
	    	flatId = request.form['flat_no']
	    	db.execute("Update housing set sale = 0 where flat_no = %s",(flatId,))
	    elif 'add' in request.form:
	    	flatId = request.form['flat_no']
	    	db.execute("Update housing set sale = 1 where flat_no = %s",(flatId,))
	    elif 'remove_rent' in request.form:
	    	flatId = request.form['flat_no']
	    	db.execute("UPDATE rent_house SET tenant_id = NULL, rent_status = 1 where flat_no = %s",(flatId,))
	    else:
	    	flatId = request.form['flat_no']
	    	if request.form['rent_status_change'] == 'ADD RENT':
	    		db.execute("INSERT INTO rent_house VALUES(%s,NULL,1)",(flatId,))
	    	else:
	    		db.execute("DELETE FROM rent_house where flat_no = %s",(flatId,))
	    db.execute("select * from house_owner where id = %s union select * from tenant where id = %s limit 50",(session["user_id"],session["user_id"]))
	    trans = db.fetchall()
	    return render_template("index.html",trans=trans)
    
@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    global lim
    """Buy shares of stock."""
    if request.method=="GET":
        lim = 51
        db.execute("select flat_no, price, square, kitchen, living, bedroom, buildingtype, constructiontime, renovationcondition, buildingstructure, elevator, subway, name, communityaverage, link, university as near, image_url from housing,districts where housing.district = districts.district and sale = 1 order by flat_no asc LIMIT 51")
        urls=db.fetchall()
        return render_template("buy.html",urls=urls)
    else:
    	if 'more' in request.form:
    	    lim = lim+51
    	    db.execute("select flat_no, price, square, kitchen, living, bedroom, buildingtype, constructiontime, renovationcondition, buildingstructure, elevator, subway, name, communityaverage, link, university as near, image_url from housing,districts where housing.district = districts.district and sale = 1 order by flat_no asc LIMIT %s",(lim,))
    	    urls=db.fetchall()
    	    return render_template("buy.html",urls=urls)

    	if 'Purchase' in request.form:
	        flatId = request.form["flat_no"]
	        print (request.form)
	        print (flatId)
	        db.execute("select price,owner from housing where flat_no = %s",(flatId,))
	        (cost,ownerId) = db.fetchone()
	        print (cost,ownerId)
	        db.execute("select cash from users where id = %s",(session["user_id"],))
	        balance = db.fetchone()[0]
	        if cost>balance:
	            return apology("Sorry","U don't have enough cash")
	            
	        # TABLE transaction_log (Transaction_ID, Stock ,Symbol, Shares , Price ,type, Time)
	        cur_time = datetime.datetime.now(pytz.timezone('US/Pacific'))
	        print (cur_time)
	        print(ownerId)
	        print(session["user_id"])
	        db.execute("BEGIN")
	        db.execute("INSERT INTO transaction_log (transaction_id,customer_id,price,type,flat_no,user_id) VALUES (%s,%s,%s,'BUY',%s,%s)",(str(uuid.uuid4()),ownerId,cost,flatId,session["user_id"]))
	        db.execute("UPDATE users SET cash=%s where id=%s",(balance-cost,session["user_id"]))
	        db.execute("select cash from users where id = %s",(ownerId,))
	        balance_owner = db.fetchone()[0]
	        db.execute("UPDATE users SET cash=%s where id=%s",(balance_owner+cost,ownerId))
	        db.execute("INSERT INTO transaction_log (transaction_id,customer_id,price,type,flat_no,user_id) VALUES (%s,%s,%s,'SOLD',%s,%s)",(str(uuid.uuid4()),session["user_id"],cost,flatId,ownerId))
	        db.execute("UPDATE housing set owner = %s where flat_no = %s",(session["user_id"],flatId))
	        db.execute("COMMIT")
	        return render_template("success.html")

    	elif ('Apply' in request.form):
		    arr = init_arr()
		    for attr in request.form:
		    	if(attr in arr):
		    		if request.form[attr] != '':
		    			if attr == 'district':
		    				arr['district'] = tuple((int(request.form[attr]),))
		    			elif attr == 'buildingstructure':
		    				arr['buildingstructure'] = tuple((int(request.form[attr]),))
		    			else:
		    				arr[attr] = request.form[attr]
		    for attr in arr:
		    	print (attr,arr[attr])
		    db.execute("select flat_no, price, square, kitchen, living, bedroom, buildingtype, constructiontime, renovationcondition, buildingstructure, elevator, subway, name, communityaverage, link, university as near, image_url from housing,districts where housing.district = districts.district and cast(kitchen as text) like %s and cast(flat_no as text) like %s and cast(living as text) like %s and price between %s and %s and cast(bedroom as text) like %s and districts.district in %s and square between %s and %s and buildingstructure in %s and cast(elevator as text) like %s and sale = 1 and university like %s limit %s",(arr['Kitchen'],arr['flat_no'],arr['Living'],arr['price_min'],arr['price_max'],arr['bedroom'],arr['district'],arr['area_min'],arr['area_max'],arr['buildingstructure'],arr['elevator'],arr['near'],lim))
		    urls=db.fetchall()
		    arr = init_arr()
		    return render_template("buy.html",urls=urls)

@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    db.execute("SELECT * FROM transaction_log WHERE user_id = %s",(session["user_id"],))
    user = db.fetchall()
    print (user)
    return render_template("history.html", user = user)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        db.execute("SELECT * FROM users WHERE username = %(user)s",{'user':request.form.get("username")})
        rows = db.fetchall()

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0][2]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0][0]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method=="GET":
        return render_template("quote.html",userId = session["user_id"])
    else:
        db.execute("select cash from users where id = %s", (session['user_id'],))
        balance = db.fetchone()[0]
        return render_template("quote.html", userId = session["user_id"], balance = balance)

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    if request.method=="POST":
        username=request.form.get("username")
        password=request.form.get("password")
        cp=request.form.get("cp")
        q=request.form.get("sq")
        a=request.form.get("sa")
        
        # validate new_user details
        if not username:
            return apology("Please Enter Username")
        if not password:
            return apology("Please Enter Password")
        if password!=cp:
            return apology("Password not matched")
        
        # add the new_user
        print('user=',str(username),'pass=',str(pwd_context.hash(password)))
        try:
            db.execute("INSERT INTO users (username,hash) VALUES(%(username)s,%(password)s)",{'username':username,'password':pwd_context.hash(password)})
            db.execute("SELECT id FROM users WHERE username=%s",(username,))
            key=db.fetchone()[0]
            print("ID =",key)
            db.execute("INSERT INTO reset (id,sq,sa) VALUES (%(key)s,%(q)s,%(a)s)",{'key':key,'q':q,'a':a})
            
            # remember which user has logged in
            session["user_id"] = key
            
            # redirect user to home page
            return redirect(url_for("index"))

        except psycopg2.IntegrityError as e:
            print("EXCEPTION CAUGHT WHILE INSERTING USER",e)
            return apology("Sorry, this username already exists")

    else:
        return render_template("register.html")

@app.route("/rent", methods=["GET", "POST"])
@login_required
def rent():
    """Sell shares of stock."""
    if request.method=="GET":
        db.execute("SELECT housing.flat_no, price, square, kitchen, living, bedroom, buildingtype, constructiontime, renovationcondition, buildingstructure, elevator, subway, name, communityaverage, link, university as near, image_url FROM housing,districts,rent_house where housing.district = districts.district and rent_status = 1 and owner != %s and housing.flat_no = rent_house.flat_no order by housing.flat_no asc LIMIT 50",(session["user_id"],))
        urls=db.fetchall()
        return render_template("rent.html",urls=urls)
    else:
    	if 'Rent' in request.form:
	        print (request.form)
	        flatId = request.form["flat_no"]
	        db.execute("select price,owner from housing where flat_no = %s",(flatId,))
	        (cost,ownerId) = db.fetchone()
	        print (cost,ownerId)
	        cost = cost*Decimal(0.3)
	        db.execute("select cash from users where id = %s",(session["user_id"],))
	        balance = db.fetchone()[0]
	        db.execute("select cash from users where id = %s",(ownerId,))
	        balance_owner = db.fetchone()[0]
	        if cost>balance:
	            return apology("Sorry","U don't have enough cash")
	            
	        # TABLE transaction_log (Transaction_ID, Stock ,Symbol, Shares , Price ,type, Time)
	        cur_time = datetime.datetime.now(pytz.timezone('US/Pacific'))
	        print (cur_time)
	        db.execute("BEGIN")
	        db.execute("INSERT INTO transaction_log (transaction_id,customer_id,price,type,flat_no,user_id) VALUES (%s,%s,%s,'RENT',%s,%s)",(str(uuid.uuid4()),ownerId,cost,flatId,session["user_id"]))
	        db.execute("UPDATE users SET cash=%s where id=%s",(balance-cost,session["user_id"]))
	        db.execute("UPDATE users SET cash=%s where id=%s",(balance_owner+cost,ownerId))
	        db.execute("INSERT INTO transaction_log (transaction_id,customer_id,price,type,flat_no,user_id) VALUES (%s,%s,%s,'RENT',%s,%s)",(str(uuid.uuid4()),session["user_id"],cost,flatId,ownerId))
	        db.execute("UPDATE rent_house set tenant_id = %s, rent_status = 0 where flat_no = %s",(int(session["user_id"]),flatId))
	        db.execute("COMMIT")
	        return render_template("success.html")

    	elif ('Apply' in request.form):
		    arr = init_arr()
		    for attr in request.form:
		    	if(attr in arr):
		    		if request.form[attr] != '':
		    			print (request.form[attr])
		    			if attr == 'district':
		    				arr['district'] = tuple((int(request.form[attr]),))
		    			elif attr == 'buildingstructure':
		    				arr['buildingstructure'] = tuple((int(request.form[attr]),))
		    			else:
		    				arr[attr] = request.form[attr]
		    for attr in arr:
		    	print (attr,arr[attr])
		    db.execute("SELECT housing.flat_no, price, square, kitchen, living, bedroom, buildingtype, constructiontime, renovationcondition, buildingstructure, elevator, subway, name, communityaverage, link, university as near, image_url from housing,districts,rent_house where housing.district = districts.district and housing.flat_no = rent_house.flat_no and cast(kitchen as text) like %s and cast(housing.flat_no as text) like %s and cast(living as text) like %s and price between %s and %s and cast(bedroom as text) like %s and districts.district in %s and square between %s and %s and buildingstructure in %s and rent_status = 1 and owner != %s and cast(elevator as text) like %s and university like %s limit 50",(arr['Kitchen'],arr['flat_no'],arr['Living'],arr['price_min'],arr['price_max'],arr['bedroom'],arr['district'],arr['area_min'],arr['area_max'],arr['buildingstructure'],session["user_id"],arr['elevator'],arr['near']))
		    urls=db.fetchall()
		    arr = init_arr()
		    return render_template("rent.html",urls=urls)

# global variable for password reset
verified_user = None 
@app.route("/verify",methods=["GET","POST"])
def verify():
    """validation of user for reset password"""
    if request.method=="GET":
        return render_template("verify.html")
    else:
        username = request.form.get("username")
        q=request.form.get("sq")
        a=request.form.get("sa")
        db.execute("SELECT * FROM users JOIN reset ON users.id = reset.id WHERE username=%s",(username))
        exist = db.fetchall()
        print(exist)
        if exist ==None:
            return apology("sorry this username doesn't exist")
        if exist[0][5]!=q:
            return apology("Wrong question selected")
        if exist[0][6]!=a:
            return apology("Wrong answer to security question ?")
            
        #store the verified_user  
        global verified_user
        verified_user=username
        
        return redirect(url_for("reset_password"))

@app.route("/reset_password",methods=["GET","POST"])
def reset_password():
    """reset password"""
    if request.method=="GET":
        return render_template("reset_password.html")
    else:
        password = request.form.get("password")
        if verified_user==None:
            return apology("sorry u are not verified")
        db.execute("UPDATE users SET hash=%s WHERE username=%s",(pwd_context.hash(password),verified_user))
        return render_template("reset_success.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)