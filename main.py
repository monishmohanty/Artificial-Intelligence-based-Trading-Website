from flask import Flask, render_template, request, redirect, url_for, session, g
import re
import cx_Oracle

import pandas as pd
import numpy as np
import fxcmpy
import time
from datetime import datetime

cx_Oracle.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_21_9")

# ------------- ALGORITHM CODE ---------------------------------------------

col = ["tradeId", "amountK", "currency", "grossPL", "isBuy"]

class ConTrader():
    def __init__(self, instrument, bar_length, window, units):
        self.instrument = instrument
        self.bar_length = pd.to_timedelta(bar_length) 
        self.tick_data = None
        self.raw_data = None
        self.data = None 
        self.ticks = 0
        self.last_bar = None  
        self.units = units
        self.position = 0
        
        #*****************add strategy-specific attributes here******************
        self.window = window
        #************************************************************************        
    
    def get_most_recent(self, period = "m1", number = 10000):
        while True:  
            time.sleep(5)
            df = api.get_candles(self.instrument, number = number, period = period, columns = ["bidclose", "askclose"])
            df[self.instrument] = (df.bidclose + df.askclose) / 2
            df = df[self.instrument].to_frame()
            df = df.resample(self.bar_length, label = "right").last().dropna().iloc[:-1]
            self.raw_data = df.copy()
            self.last_bar = self.raw_data.index[-1]
            if pd.to_datetime(datetime.utcnow()) - self.last_bar < self.bar_length:
                break
    
    def get_tick_data(self, data, dataframe):
        
        self.ticks += 1
        print(self.ticks, end = " ", flush = True)
        
        recent_tick = pd.to_datetime(data["Updated"], unit = "ms")
        
        # stop trading when a key event occurs
      
        if recent_tick - self.last_bar > self.bar_length:
            self.tick_data = dataframe.loc[self.last_bar:, ["Bid", "Ask"]]
            self.tick_data[self.instrument] = (self.tick_data.Ask + self.tick_data.Bid)/2
            self.tick_data = self.tick_data[self.instrument].to_frame()
            self.resample_and_join()
            self.define_strategy() 
            self.execute_trades()
            
    def resample_and_join(self):
        self.raw_data = self.raw_data.append(self.tick_data.resample(self.bar_length, 
                                                             label="right").last().ffill().iloc[:-1])
        self.last_bar = self.raw_data.index[-1]  
        
    def define_strategy(self): # "strategy-specific"
        df = self.raw_data.copy()
        
        #******************** define your strategy here ************************
        df["returns"] = np.log(df[self.instrument] / df[self.instrument].shift())
        df["position"] = -np.sign(df.returns.rolling(self.window).mean())
        #***********************************************************************
        
        self.data = df.copy()
    
    def execute_trades(self):
        if self.data["position"].iloc[-1] == 1:
            if self.position == 0:
                order = api.create_market_buy_order(self.instrument, self.units)
                self.report_trade(order, "GOING LONG")  
            elif self.position == -1:
                order = api.create_market_buy_order(self.instrument, self.units * 2)
                self.report_trade(order, "GOING LONG")  
            self.position = 1
        elif self.data["position"].iloc[-1] == -1: 
            if self.position == 0:
                order = api.create_market_sell_order(self.instrument, self.units)
                self.report_trade(order, "GOING SHORT")  
            elif self.position == 1:
                order = api.create_market_sell_order(self.instrument, self.units * 2)
                self.report_trade(order, "GOING SHORT")  
            self.position = -1
        elif self.data["position"].iloc[-1] == 0: 
            if self.position == -1:
                order = api.create_market_buy_order(self.instrument, self.units)
                self.report_trade(order, "GOING NEUTRAL")  
            elif self.position == 1:
                order = api.create_market_sell_order(self.instrument, self.units)
                self.report_trade(order, "GOING NEUTRAL")  
            self.position = 0

    def report_trade(self, order, going):  
        time = order.get_time()
        units = api.get_open_positions().amountK.iloc[-1]
        price = api.get_open_positions().open.iloc[-1]
        unreal_pl = api.get_open_positions().grossPL.sum()
        print("\n" + 100* "-")
        print("{} | {}".format(time, going))
        print("{} | units = {} | price = {} | Unreal. P&L = {}".format(time, units, price, unreal_pl))
        print(100 * "-" + "\n")

# ------------- ALGORITHM CODE ENDS---------------------------------------------

#connecting to database
app = Flask(__name__)

app.secret_key= 'your secret key'

#oracle port : 1521
#sid : rhea
#password : rheapaul2002
#user : sys

DB_USER = "SYSTEM"
DB_PASSWORD = "rheapaul2002"
DB_HOST = "localhost"
DB_PORT = "1521"
DB_SERVICE = "xe"

#CONNECT TO database IDENTIFIED BY user USING "password";

def get_connection():
    dsn = cx_Oracle.makedsn(DB_HOST, DB_PORT, service_name=DB_SERVICE)
    connection = cx_Oracle.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn)
    return connection

#connecting webpages
#all html templates placed in html
#redirects to /template/name.html

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/sign_log")
def sign_log():
    return render_template("sign_log.html")



@app.route('/login', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form: 
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists
        connection = get_connection()
        cursor = connection.cursor()
        query = "SELECT COUNT(*) FROM Usert WHERE user_name = :username and password = :password"
        cursor.execute(query, {'username': username, 'password': password})
        account = cursor.fetchone()[0]
        # If account exists show error and validation checks
        if account > 0:
        #     # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session["username"] = username
        #     # Redirect to home page
            return redirect(url_for('dashboard'))
        else:
        #     # Login failed, render the login page with an error message
            error_message = "Invalid username or password"
            return render_template("login.html", error_message=error_message)
    else:
        # Render the login page
        return render_template("login.html", msg=msg)

@app.route('/login/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))

@app.route('/login/sign_up', methods=['GET', 'POST'])
def sign_up():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        password2 = request.form['password2']
        email = request.form['email']
        pan_number = request.form['pan_number']
        phone_number = request.form['phone_number']
        forex_id = request.form['forex_id']
        api_key = request.form['api_key']

        # data = [[NULL],['password'],['username'], ['pan_number'],['phone_number'], ['email'], ['forex_id'], ['api_key']]

        # Check if account exists using MySQL
        connection = get_connection()
        cursor = connection.cursor()
        query = "SELECT COUNT(*) FROM Usert WHERE user_name = :username"
        cursor.execute(query, {'username': username})
        account = cursor.fetchone()[0]
        # If account exists show error and validation checks
        if account > 0:
            msg = 'User Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not re.match(password2, password):
            msg = 'Check password again!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO Usert(password, user_name, pan_number, phone_number, email, forex_id, api_key) VALUES(:password, :username, :pan_number, :phone_number, :email, :forex_id, :api_key)', {"password" : password, "username" : username, "pan_number" : pan_number, "phone_number" : phone_number, "email" : email, "forex_id" : forex_id, "api_key" : api_key})
            cursor.execute("SELECT * FROM Usert WHERE user_name = :username", {"username": username})
            usid = cursor.fetchone()
            userid  = usid[0] 
            print(userid)
            cursor.execute('INSERT INTO Stock_Usert(Symbol, User_ID, Ask, Bid, Time) VALUES(:stock, :userid, :ask, :bid, CURRENT_TIMESTAMP)', {"stock" : 0, "userid" : userid, "ask" : 0, "bid" : 0})
            cursor.execute('INSERT INTO Stock_Usert(Symbol, User_ID, Ask, Bid, Time) VALUES(:stock, :userid, :ask, :bid, CURRENT_TIMESTAMP)', {"stock" : 10, "userid" : userid, "ask" : 0, "bid" : 0})
            cursor.execute('INSERT INTO Stock_Usert(Symbol, User_ID, Ask, Bid, Time) VALUES(:stock, :userid, :ask, :bid, CURRENT_TIMESTAMP)', {"stock" : 11, "userid" : userid, "ask" : 0, "bid" : 0})
            cursor.execute('INSERT INTO Stock_Usert(Symbol, User_ID, Ask, Bid, Time) VALUES(:stock, :userid, :ask, :bid, CURRENT_TIMESTAMP)', {"stock" : 12, "userid" : userid, "ask" : 0, "bid" : 0})
            connection.commit()
            msg = 'You have successfully registered!'


    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('sign_up.html', msg=msg)

@app.route("/dashboard")
def dashboard():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        def get_balance():
            # obtain current balance
            #api = fxcmpy.fxcmpy(access_token='3f0208b029828c33dc352151c36ac4def053df7b', log_level='error', server='demo')
            #balance = api.get_accounts().balance
            balance = 34553
            #return balance[0]
            return balance

        balance = get_balance()

        connection = get_connection()
        cursor = connection.cursor()
        # Update the user's account balance in the database
        cursor.execute("SELECT * FROM Usert WHERE user_name = :username", {"username": session["username"]})
        row = cursor.fetchone()
        userid = row[0]
        cursor.execute("UPDATE Usert SET account_balance = :balance WHERE user_name = :username", {"balance" : balance, "username": session["username"]})
        cursor.execute("SELECT * FROM Stock_Usert WHERE User_ID = :userid", {"userid": userid})
        row = cursor.fetchall()
        stock_list = {
            'symbol1' : row[-1][0],
            'ask1' : row[-1][1],
            'bid1' : row[-1][2],
            'time1' : row[-1][3],
            'symbol2' : row[-2][0],
            'ask2' : row[-2][1],
            'bid2' : row[-2][2],
            'time2' : row[-2][3],
            'symbol3' : row[-3][0],
            'ask3' : row[-3][1],
            'bid3' : row[-3][2],
            'time3' : row[-3][3],
            'symbol4' : row[-4][0],
            'ask4' : row[-4][1],
            'bid4' : row[-4][2],
            'time4' : row[-4][3],
        }

        # cursor.execute('INSERT INTO Algorithms(Algorithm_ID, Algorithm_Name, Last_Updated, Profit) VALUES(:iid, :algname, CURRENT_TIMESTAMP, :profit)', {"iid" : 1, "algname" : 'SimpleMovingAvg', "profit" : 10})
        # cursor.execute('INSERT INTO Algorithms(Algorithm_ID, Algorithm_Name, Last_Updated, Profit) VALUES(:iid, :algname, CURRENT_TIMESTAMP, :profit)', {"iid" : 2, "algname" : 'KalmanFilteredSMA', "profit" : 30})
        # cursor.execute('INSERT INTO Algorithms(Algorithm_ID, Algorithm_Name, Last_Updated, Profit) VALUES(:iid, :algname, CURRENT_TIMESTAMP, :profit)', {"iid" : 3, "algname" : 'ExpMovingAverage', "profit" : 10})
        # cursor.execute('INSERT INTO Algorithms(Algorithm_ID, Algorithm_Name, Last_Updated, Profit) VALUES(:iid, :algname, CURRENT_TIMESTAMP, :profit)', {"iid" : 4, "algname" : 'BollingerBands', "profit" : 40})

        connection.commit()
        
        cursor.execute("SELECT * FROM Algorithms")
        alg = cursor.fetchall()
        print(alg)
        algo_list = {
            'algoid1' : alg[0][0],
            'algoname1' : alg[0][1],
            'time1' : alg[0][2],
            'profit1' : alg[0][3],

            'algoid2' : alg[2][0],
            'algoname2' : alg[2][1],
            'time2' : alg[2][2],
            'profit2' : alg[2][3],

            'algoid3' : alg[3][0],
            'algoname3' : alg[3][1],
            'time3' : alg[3][2],
            'profit3' : alg[3][3],

            'algoid4' : alg[1][0],
            'algoname4' : alg[1][1],
            'time4' : alg[1][2],
            'profit4' : alg[1][3]
        }
        connection.commit()
        return render_template('dashboard.html', username=session['username'], balance=balance, stock_list=stock_list, algo_list=algo_list)
        # algo_list=algo_list
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route("/dashboard/account")
def account():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Usert WHERE user_name = :username", {"username": session["username"]})
    row = cursor.fetchone()

    user = {
        'username' : row[2],
        'pan_number' : row[3],
        'phone_number' : row[5],
        'email' : row[6],
        'forex_id' : row[7],
        'api_key' : row[8]
    }

    return render_template("account.html", user=user)

@app.route('/dashboard/stock', methods=['GET', 'POST'])
def stock():
    # Output message if something goes wrong...
    msg = ''
    username = session['username']
    print(username)
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Usert WHERE user_name = :username", {"username": session["username"]})
    row = cursor.fetchone()
    userid = row[0]
    # query1 = "SELECT User_ID FROM Usert WHERE user_name = :username"
    print(userid)
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST': 
        # Create variables for easy access

        if 'stock' in request.form:
            stock = request.form['stock']
            #print(stock)
            def get_bid_ask_spread(stock):
                # api = fxcmpy.fxcmpy(access_token='3f0208b029828c33dc352151c36ac4def053df7b', log_level='error', server='demo')
                # api.subscribe_market_data(stock)
                # bid = api.get_last_price(stock).Bid
                # ask = api.get_last_price(stock).Ask
                # spread = ask - bid
                stock = stock.upper()
                bid = 1
                ask = 3
                spread = 1
                return stock, bid, ask, spread
            a = get_bid_ask_spread(stock)

            stock = a[0]
            bid = a[1]
            ask = a[2]
            spread = a[3]
    
            #CREATE TABLE Stock_Usert(Symbol varchar(4), Ask number(10,2), Bid number(10,2), Time Timestamp, user_name varchar(20) REFERENCES Usert) ;
            #Check if there is existing Stock by the same user, if yes, update the stock, bid, ask, spread, if not, insert new stock, bid, ask, spread
            query = "SELECT COUNT(*) FROM Stock_Usert WHERE User_ID = :userid and Symbol =:stock"
            cursor.execute(query, {"userid": userid, "stock" : stock})
            account = cursor.fetchone()[0]
            # If account exists show error and validation checks
            if account > 0:
                #cursor.execute("UPDATE Stock_Usert SET Symbol = :stock, Ask= :ask, Bid= :bid WHERE user_name = :username", {"stock" : stock, "ask" : ask, "bid" : bid "username": session["username"]})
                cursor.execute("UPDATE Stock_Usert SET Ask= :ask, Bid= :bid WHERE User_ID = :userid and Symbol =:stock ", {"stock" : stock, "userid" : userid, "ask" : ask, "bid" : bid})
            else:
                # Account doesnt exists and the form data is valid, now insert new account into accounts table
                cursor.execute('INSERT INTO Stock_Usert(Symbol, User_ID, Ask, Bid, Time) VALUES(:stock, :userid, :ask, :bid, CURRENT_TIMESTAMP)', {"stock" : stock, "userid" : userid, "ask" : ask, "bid" : bid})
            connection.commit()
        user = {
            'stock' : a[0],
            'bid' : a[1],
            'ask' : a[2],
            'spread' : a[3]
        }

              
        return redirect(url_for('dashboard'))
    else:
        # Render the login page
        return render_template("stock.html")

@app.route("/dashboard/profile", methods=["GET", "POST"])
def profile():
    connection = get_connection()
    cursor = connection.cursor()

    if request.method == "GET":
        # Get the user's information from the database
        cursor.execute("SELECT * FROM Usert WHERE user_name = :username", {"username": session["username"]})
        result = cursor.fetchone()
        return render_template("profile.html", user=result)
        
    elif request.method == "POST":
        if 'update' in request.form:
            # Get form data
            username = request.form["username"]
            password = request.form["password"]
            phone_number = request.form['phone_number']
            forex_id = request.form['forex_id']
            api_key = request.form['api_key']

            # Update the user's information in the database
            cursor.execute("UPDATE Usert SET user_name = :username, password = :password, phone_number = :phone_number, forex_id = :forex_id, api_key = :api_key WHERE user_name = :old_username",
                   {"username": username, "password": password, "phone_number" : phone_number, "forex_id" : forex_id, "api_key" : api_key, "old_username": session["username"]})
            connection.commit()

            return render_template('updated.html')

        elif 'delete' in request.form:
            # Delete the user's account from the database
            cursor.execute("SELECT * FROM Usert WHERE user_name = :username", {"username": session["username"]})
            usid = cursor.fetchone()
            userid  = usid[0] 
            print(userid)

            cursor.execute("DELETE FROM Stock_Usert WHERE User_ID = :userid", {"userid": userid})
            cursor.execute("DELETE FROM Usert WHERE user_name = :username", {"username": session["username"]})

            connection.commit()

            return render_template('deleted.html')

@app.route("/dashboard/connection", methods=["GET", "POST"])
def connection():
    try:
            api = fxcmpy.fxcmpy(access_token='3f0208b029828c33dc352151c36ac4def053df7b', log_level='error', server='demo')
    except:
            status = "Not Connected"
            return status
    else:
            status = "Connected"
            return status





if __name__ == "__main__":
    app.run(debug=True)
    # api = fxcmpy.fxcmpy(config_file = "FXCM.cfg")
    # trader = ConTrader("EUR/USD", bar_length = "1min", window = 1, units = 100)
    # trader.get_most_recent()
    # api.subscribe_market_data(trader.instrument, (trader.get_tick_data, ))

