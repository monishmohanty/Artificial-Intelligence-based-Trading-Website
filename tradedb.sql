CREATE TABLE Algorithms(Algorithm_ID varchar(10) PRIMARY KEY, Algorithm_Name varchar(20), Last_Updated date, Profit number(10,4));
SELECT * FROM Algorithms;

CREATE TABLE Usert(User_ID varchar(16) PRIMARY KEY, Password varchar(8), user_name varchar(20), Pan_number varchar(10), Account_Balance number(10,2), Phone_Number number(10), Email varchar(30), forex_id varchar(20), api_key varchar(20));
SELECT * FROM Usert;

CREATE TABLE Transactions(Transaction_ID varchar(10) PRIMARY KEY, Time Timestamp, Company varchar(10), Algorithm_ID varchar(10) REFERENCES Algorithms);
SELECT * FROM Transactions;

CREATE TABLE Stock_Usert(Symbol varchar(4), Ask number(10,2), Bid number(10,2), Time Timestamp, User_ID varchar(16) REFERENCES Usert, PRIMARY KEY(User_ID, Symbol) ) ;
SELECT * FROM Stock_Usert

CREATE TABLE User_Algo(User_ID varchar(16) REFERENCES Usert, Time_Stamp date, Algorithm_ID varchar(10) REFERENCES Algorithms, Realize_Profits number(10,4), PRIMARY KEY(User_ID, Algorithm_ID, Time_Stamp) );
SELECT * FROM User_Algo;


#To auto increment user id 

CREATE SEQUENCE user_id_seq;

CREATE TRIGGER user_bi
BEFORE INSERT ON Usert
FOR EACH ROW
BEGIN
  SELECT user_id_seq.nextval
  INTO :new.user_id
  FROM dual;
END;


INSERT INTO Usert VALUES ('1','1234567','me','1234567', 2012.11, 1234567,'me@gmail.com','2212345678','123');
SELECT * FROM Usert;


INSERT INTO Stock_Usert(Symbol, User_ID, Ask, Bid, Time) VALUES('YO', '2', '25', '11', CURRENT_TIMESTAMP);

INSERT INTO Algorithms(Algorithm_ID, Algorithm_Name, Last_Updated, Profit) VALUES('1', 'SimpleMovingAverage', CURRENT_TIMESTAMP, '10');
INSERT INTO Algorithms(Algorithm_ID, Algorithm_Name, Last_Updated, Profit) VALUES('2', 'KalmanFilteredSMA', CURRENT_TIMESTAMP, '30');
INSERT INTO Algorithms(Algorithm_ID, Algorithm_Name, Last_Updated, Profit) VALUES('3', 'ExpMovingAverage', CURRENT_TIMESTAMP, '60');
INSERT INTO Algorithms(Algorithm_ID, Algorithm_Name, Last_Updated, Profit) VALUES('4', 'BollingerBands', CURRENT_TIMESTAMP, '40');


SELECT * FROM Usert;
SELECT * FROM Stock_Usert;
SELECT * FROM Transactions;
SELECT * FROM Algorithms;
SELECT * FROM User_Algo;

CREATE TABLE Stock_Usert(Symbol varchar(4), Ask number(10,2), Bid number(10,2), Time Timestamp, User_ID varchar(16) REFERENCES Usert) ;