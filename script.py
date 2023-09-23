import cx_Oracle
cx_Oracle.init_oracle_client(lib_dir=r"C:\instantclient_21_8")

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

connection = get_connection()
cursor = connection.cursor()

cursor.execute("INSERT INTO Usert VALUES ('1','1234567','me','1234567', 2012.11, 1234567,'me@gmail.com','2212345678','123')")
connection.commit()