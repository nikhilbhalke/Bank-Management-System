'''
    Author Harsh Nandwani
'''

from flask import *
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime, time
import pytz

app = Flask(__name__)

#-----Databse URI-----
#This project uses a Postgresql database, located on heroku server
# Pages might load slower as we're using a free hosting 

app.config['SQLALCHEMY_DATABASE_URI']="postgres://cpzolzwcpdnjro:c90ebb866bb410d992523c388e05d10d049f13aebe9a32206a13764fbe885fbd@ec2-3-222-30-53.compute-1.amazonaws.com:5432/d8tanof6niifrn"
db = SQLAlchemy(app)

# Setting the Flask app's secret_key to use sessions.
app.secret_key= "harsh"

#Initializing the timezone to IST +05:30
timezone=pytz.timezone("Asia/Calcutta")

# Creating databse table models 

class Login(db.Model):
    
    '''
        The Login Table stores login data of both Account executives and Cashiers
    '''
    __tablename__ = "Userstore"
    
    UserId = db.Column(db.String(), primary_key=True)
    Password = db.Column(db.String(),nullable=False)
    Role = db.Column(db.String(),nullable=False)

class CustomerDetails(db.Model):
    
    __tablename__ = "CustomerDetails"

    CustomerId = db.Column(db.Integer,primary_key=True)
    SSNID = db.Column(db.Integer,nullable=False)
    Name = db.Column(db.String(),nullable=False)
    Age = db.Column(db.Integer,nullable=False)
    DOB = db.Column(db.DateTime)
    Sex = db.Column(db.String(1))
    Email = db.Column(db.String())
    ContactNumber = db.Column(db.Integer)
    Address = db.Column(db.String())
    City = db.Column(db.String())
    State = db.Column(db.String())
    Pincode = db.Column(db.Integer)
    Status = db.Column(db.String())
    Message = db.Column(db.String())
    LastUpdated = db.Column(db.DateTime)
    db.UniqueConstraint(SSNID)

class AccountDetails(db.Model):
    __tablename__='AccountDetails'

    AccountId = db.Column(db.Integer,primary_key=True)
    CustomerId = db.Column(db.Integer, db.ForeignKey('CustomerDetails.CustomerId'))
    AccountType = db.Column(db.String(1),nullable=False)
    Amount = db.Column(db.Float,nullable=False)
    LastTransaction = db.Column(db.DateTime)
    Status = db.Column(db.String())
    db.UniqueConstraint(CustomerId,AccountType)

class Transactions(db.Model):
    __tablename__='Transactions'

    TransactionId = db.Column(db.Integer,primary_key=True)
    AccountId = db.Column(db.Integer, db.ForeignKey('AccountDetails.AccountId'))
    TransactionType = db.Column(db.String())
    TransactionAmount = db.Column(db.Float,nullable=False)
    DateTime = db.Column(db.DateTime,nullable=False)
    Description = db.Column(db.String())

#Defining various app routes

@app.route("/",methods=['GET','POST'])
@app.route("/index",methods=['GET','POST'])
def index():

    if 'userid' in session:
        # Checking if session userid is already set

        ##print(session['userid'])
        if session['role']=='executive':
            return redirect(url_for('executive_home'))
        else:
            return redirect(url_for("CashierHome"))

    if request.method=='POST':
        # When form is submited capture username and password from the web page and check for it in the database
        username= request.form.get('username')
        password = request.form.get('password')
        currentUser = Login.query.filter_by(UserId=username).first()
        if currentUser is not None:
            if currentUser.Password == password:
                # The username and password are valid, create a session
                session['userid']=username
                session['role']=currentUser.Role
                
                if session['role']=='executive':
                    return redirect(url_for('executive_home'))
                else:
                    return redirect(url_for("CashierHome"))

            else:
                return render_template('index.html',message="WrongPassword!")
        else:
            return render_template('index.html',message="Invalidusername")
    return render_template('index.html')   

@app.route('/Executive/Home')
def executive_home():
    # Check if anyone is accesing the url directly without valid login
    if 'userid' not in session:
        return redirect(url_for("index"))

    return render_template('exehome.html')

@app.route("/Executive/CreateCustomer",methods=['POST','GET'])
def create_customer():
    if 'userid' not in session:
        return redirect(url_for("index"))

    if request.method=='POST':
        SSNID = request.form.get("ssn-id")
        customerName = request.form.get("cust-name")
        age = request.form.get("age")
        address = request.form.get("address")
        state = request.form.get("state")
        city = request.form.get("city")
        mCustomer = CustomerDetails(SSNID=SSNID,Name=customerName,Age=age,Address=address,State=state,City=city,Status='Active',Message='Customer Created Successfully',LastUpdated=datetime.now(timezone))
        db.session.add(mCustomer)
        try:
            db.session.commit()
            return render_template("custcreate.html",message="Successful")
        except IntegrityError:
            return render_template("custcreate.html",message="SSN Exists")

    return render_template("custcreate.html")

@app.route("/Executive/UpdateCustomer")
def update_customer():

    if 'userid' not in session:
        return redirect(url_for("index"))

    return render_template("custupdate.html")

@app.route("/Executive/DeleteCustomer",methods=['GET','POST'])
def Delete():

    if 'userid' not in session:
        return redirect(url_for("index"))

    if request.method=='POST':
        custId=request.form.get('cust-id')
        print(custId)
        customer = CustomerDetails.query.filter_by(CustomerId=custId).first()
        if customer is None:
            return render_template('custdelete.html',message='invalid')
        accounts = AccountDetails.query.filter_by(CustomerId=custId).all()
        for a in accounts:
            trans = Transactions.query.filter_by(AccountId=a.AccountId).all()
            for t in trans:
                db.session.delete(t)
            db.session.delete(a)
        db.session.delete(customer)
        db.session.commit()
        return render_template('custdelete.html',message='Successful')

    return render_template('custdelete.html')


@app.route("/Executive/CreateAccount",methods=['GET','POST'])
def CreateAccount():

    if 'userid' not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        cId = request.form.get("cust-id")
        accType = request.form.get("type")
        atype=accType[0]
        amount = request.form.get("amount")
        time = datetime.now(timezone)

        mAccount = AccountDetails(CustomerId=cId,AccountType=atype,Amount=amount,LastTransaction=time,Status='Active')
        db.session.add(mAccount)
        try:
            db.session.commit()
            depositTransaction = Transactions(AccountId=mAccount.AccountId,TransactionType='Credit',TransactionAmount=mAccount.Amount,DateTime=time,Description="Account opening deposit")
            db.session.add(depositTransaction)
            db.session.commit()
            return render_template("accreate.html",message="Successful")
        except IntegrityError as e:
            if "violates unique constraint \"AccountDetails_CustomerId_AccountType_key\"" in str(e):
                return render_template("accreate.html",message="Exists")
            else:
                return render_template("accreate.html",message="Invalid Customer Id!")

    return render_template('accreate.html')


@app.route("/Executive/DeleteAccount",methods=['GET','POST'])
def DeleteAccount():

    if 'userid' not in session:
        return redirect(url_for("index"))

    if request.method=='POST':
        accId = request.form.get('acc-id')
        account = AccountDetails.query.filter_by(AccountId=accId).first()
        if account is None:
            return render_template('accdelete.html',message='invalid')
        allTran = Transactions.query.filter_by(AccountId=accId).all()
        for t in allTran:
            db.session.delete(t)
        db.session.commit()
        db.session.delete(account)
        db.session.commit()
        return render_template('accdelete.html',message='successful')

    return render_template('accdelete.html')


@app.route("/Executive/AccountStatus")
def AccountStatus():
    if 'userid' not in session:
        return redirect(url_for("index"))

    accountsData = AccountDetails.query.all()
    return render_template('accstatus.html',accounts=accountsData)


@app.route("/Executive/CustomerStatus")
def CustomerStatus():

    if 'userid' not in session:
        return redirect(url_for("index"))

    customersData = CustomerDetails.query.all()
    return render_template('custstatus.html',customers=customersData)


@app.route("/Cashier/Home",methods=['GET','POST'])
def CashierHome():

    if 'userid' not in session:
        return redirect(url_for("index"))

    if request.method=='POST':

        custId = request.form.get("cust-id")
        if custId =="":
            accId = request.form.get("acc-id")
            if accId =="":
                return render_template('cashierhome.html',message="EnterId")
            else:
                account = AccountDetails.query.filter_by(AccountId=accId).first()
                if account is None:
                    return render_template('cashierhome.html',message="invalid")
                return redirect(url_for('ViewAccountDetailsByAccId',accId=account.AccountId))
        else:
            cust = AccountDetails.query.filter_by(CustomerId=custId).first()
            if cust is None:
                return render_template('cashierhome.html',message="invalid")
            return redirect(url_for('ViewAccountDetailsByAccId',accId=cust.AccountId))
        
    return render_template('cashierhome.html')


@app.route("/Cashier/AccountDetails/<int:accId>")
def ViewAccountDetailsByAccId(accId):

    if 'userid' not in session:
        return redirect(url_for("index"))
    
    accountData = AccountDetails.query.filter_by(AccountId=accId).first()
    return render_template('accdetails.html',account=accountData)

@app.route("/Cashier/AccountDetails")
def ViewAccountDetails():

    if 'userid' not in session:
        return redirect(url_for("index"))
    return render_template('accdetails.html')


@app.route("/Cashier/GetAccountStatement",methods=['GET','POST'])
def GetAccountStatement():

    if 'userid' not in session:
        return redirect(url_for("index"))

    if request.method=='POST':
        accountId=request.form.get("acc-id")
        noOfTran = request.form.get("noOfTran")
        tranData = Transactions.query.filter_by(AccountId=accountId).order_by(Transactions.DateTime.desc()).limit(int(noOfTran)).all()
        if tranData==[]:
            return render_template('accstatement.html',message="WrongAcc")
        else:
            return render_template('accstatement2.html',transactions=tranData)
    return render_template('accstatement.html')


@app.route("/Cashier/AccountStatement")
def AccountStatement():

    if 'userid' not in session:
        return redirect(url_for("index"))

    return render_template('accstatement.html')


@app.route("/Cashier/Deposit")
@app.route("/Cashier/Withdraw")
@app.route("/Cashier/Transfer")
def goToAccDetails():
   # return redirect(url_for("ViewAccountDetails"))
   return render_template("CashierHome.html")

@app.route("/Cashier/Deposit/<int:accId>",methods=['GET','POST'])
def Deposit(accId):

    if 'userid' not in session:
        return redirect(url_for("index"))

    currentAccount = AccountDetails.query.filter_by(AccountId=accId).first()

    if request.method=="POST":
        depositAmount=request.form.get("depositAmt")
        time=datetime.now(timezone)
        depositTransaction = Transactions(AccountId=accId,TransactionType='Credit',TransactionAmount=depositAmount,DateTime=time,Description="Deposited through cashier")
        db.session.add(depositTransaction)
        currentAccount.Amount+=float(depositAmount)
        currentAccount.LastTransaction=time
        db.session.commit()
        return redirect(url_for("ViewAccountDetailsByAccId",accId=accId,message="Deposit_successful"))
    if currentAccount is None:
        return redirect(url_for("ViewAccountDetails"))
    else:
        return render_template('deposit.html',account=currentAccount)


@app.route("/Cashier/Withdraw/<int:accId>",methods=['GET','POST'])
def Withdraw(accId):

    if 'userid' not in session:
        return redirect(url_for("index"))

    currentAccount = AccountDetails.query.filter_by(AccountId=accId).first()

    if request.method=="POST":
        withdrawAmount=request.form.get("withdrawAmount")
        withdrawAmount=float(withdrawAmount)
        time=datetime.now(timezone)
        if withdrawAmount>currentAccount.Amount:
            x=0
        else:
            withdrawTransaction = Transactions(AccountId=accId,TransactionType='Debit',TransactionAmount=withdrawAmount,DateTime=time,Description="Amount Withdrawn through cashier")
            db.session.add(withdrawTransaction)
            currentAccount.Amount-=float(withdrawAmount)
            currentAccount.LastTransaction=time
            db.session.commit()
            return redirect(url_for("ViewAccountDetailsByAccId",accId=accId,message="Withdraw_successful"))
    
    if currentAccount is None:
        return redirect(url_for("ViewAccountDetails"))
    else:
        return render_template('withdraw.html',account=currentAccount)


@app.route("/Cashier/Transfer/<int:accId>",methods=['GET','POST'])
def Transfer(accId):

    if 'userid' not in session:
        return redirect(url_for("index"))

    currentAccount = AccountDetails.query.filter_by(AccountId=accId).first()

    if request.method=="POST":
        targetAcc = request.form.get("targetAcc")
        transferAmount = request.form.get("transferAmount")
        targetAccount = AccountDetails.query.filter_by(AccountId=targetAcc).first()
        time=datetime.now(timezone)
        transferAmount=float(transferAmount)
        targetAcc=float(targetAcc)
        if transferAmount>currentAccount.Amount:
            return render_template('transfer.html',account=currentAccount,message="Low Balance")
        elif targetAccount is None:
            return render_template('transfer.html',account=currentAccount,message="Invalid Target account")
        else:
            sourceDebit = Transactions(AccountId=currentAccount.AccountId,TransactionType='Debit',TransactionAmount=transferAmount,DateTime=time,Description="Transfer towards account: "+str(targetAcc))
            db.session.add(sourceDebit)
            currentAccount.Amount-=float(transferAmount)
            targetCredit = Transactions(AccountId=targetAccount.AccountId,TransactionType='Credit',TransactionAmount=transferAmount,DateTime=time,Description="Credited by transfer from "+str(currentAccount.AccountId))
            db.session.add(targetCredit)
            targetAccount.Amount+=float(transferAmount)
            db.session.commit()
            return redirect(url_for('ViewAccountDetailsByAccId',accId=currentAccount.AccountId,message="TransferSucessful"))
    if currentAccount is None:
        return redirect(url_for("ViewAccountDetails"))
    else:
        return render_template('transfer.html',account=currentAccount)

@app.route("/Logout")
def executive_logout():
    if 'userid' in session:
        session.pop('userid')
        session.pop('role')
        return redirect(url_for("index"))
    else:
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)