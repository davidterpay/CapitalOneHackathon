from flask import Flask, jsonify, redirect, render_template, request, send_file, session, url_for, g, flash

import webbrowser
from splitwise import Splitwise
from splitwise.expense import Expense
from splitwise.user import ExpenseUser
from splitwise.group import Group
from splitwise.user import User
import time
import datetime
import json
import random
import re


consumer_key = 'bj8aCMM3gXkjrFR069MfN7zP0gOGHd0s1VaXjXuk'
secret_key = 'PENzjkuDLPG378BdvdXfOHOcWw4V0cmscIA5slqr'
app = Flask(__name__)
app.secret_key = "test_secret_key"

@app.route("/")
def index():
    return render_template("welcome.html")

@app.route("/home")
def home():
	return render_template("home.html")

@app.route("/login", methods = ["POST"])
def login():
	sObj = Splitwise(consumer_key, secret_key)
	url, secret = sObj.getAuthorizeURL()
	session['secret'] = secret
	firstName = request.form.get("fname")
	lastName = request.form.get("lname")
	email = request.form.get("email")
	print(firstName,lastName,email)
	##cur.execute("INSERT INTO UserAccounts VALUES(NULL,76235, email, firstName, lastName, 0, 0)")
	##cnx.commit()

	return redirect(url)

@app.route("/calculate", methods = ['POST'])
def calculate():
	print("hello")
	jsdata = request.form['javascript_data']
	print(jsdata)
	result = re.findall('<div contenteditable="">(.*?)</div>',jsdata)
	print(result)
	roommates = ["David", "Daran", "Ram"]
	description = None
	payer = None
	price = None
	tags = None
	#clear()
	for i in range(len(result)/6):
		description = result[6*i+2]
		payer = result[6*i+4]
		price = result[6*i+3]
		tags = []
		for j in range(len(result[6*i+5])):
			print(j)
			tags.append(roommates[int(result[6*i+5][j])-1])
		transaction(description, 'The Room',payer, float(price), tags)
	print(balances())
	return render_template("home.html")

@app.route("/authorize")
def authorize():
    if 'secret' not in session:
        return redirect(url_for("home"))
    oauth_token  = request.args.get('oauth_token')
    oauth_verifier = request.args.get('oauth_verifier')
    sObj = Splitwise(consumer_key, secret_key)
    access_token = sObj.getAccessToken(oauth_token,session['secret'],oauth_verifier)
    session['access_token'] = access_token
    sObj.setAccessToken(session['access_token'])
    ram = ['Ram','Muthukumaran', 'rammk1999@gmail.com']
    david = ["David",'Terpay','david.terpay@gmail.com']
    # createGroup([[sObj.getCurrentUser().getFirstName(),sObj.getCurrentUser().getLastName(), sObj.getCurrentUser().getEmail()],ram,david], "The Room")
    return redirect(url_for("home"))

@app.route("/friends")
def friends():
    if 'access_token' not in session:
        return redirect(url_for("home"))
    sObj = Splitwise(consumer_key, secret_key)
    sObj.setAccessToken(session['access_token'])
    me = ['David', 'Terpay', 'david.terpay@gmail.com']
    ram = ['Ram', 'Muthukumaran', 'rammk1999@gmail.com']
    # transaction("pie",'Testing2','David', 10,['David','Ram'])
    print(groupMembersString('Testing2'))
    # print(sObj.getGroups())
    friends = sObj.getFriends()
    return render_template("friends.html",friends=friends)

@app.route("/newroommate", methods = ["POST"])
def addRoommate():
	firstName = request.form.get("fname")
	lastName = request.form.get("lname")
	email = request.form.get("email")
	print(firstName,lastName,email)
	addUser(firstName,lastName,email)
	return redirect("/home")

def clear():
   sObj = Splitwise(consumer_key, secret_key)
   sObj.setAccessToken(session['access_token'])
   expenses = sObj.getExpenses()
   for expense in expenses:
       expense.setCost(0)

def groupMembersString(groupName):
    sObj = Splitwise(consumer_key, secret_key)
    sObj.setAccessToken(session['access_token'])
    friends = None
    for group in sObj.getGroups():
        if group.getName() == groupName:
            friends = group
    return [friend.getFirstName() + ' ' + friend.getLastName() for friend in friends.getMembers()]

def createUser(firstName, lastName, email):
    user = User()
    user.setFirstName(firstName)
    user.setLastName(lastName)
    user.setEmail(email)
    return user

def balances():
	sObj = Splitwise(consumer_key, secret_key)
	sObj.setAccessToken(session['access_token'])
	friends = sObj.getFriends()
	amount = []
	for friend in friends:
		for balance in friend.getBalances():
			amount.append(balance.getAmount())
	return amount

def addUser(first,last,email):
   sObj = Splitwise(consumer_key, secret_key)
   sObj.setAccessToken(session['access_token'])
   user = createUser(first,last,email)
   groups = sObj.getGroups()
   for group in groups:
       if group.getName() == 'The Room':
           group.setMembers(group.getMembers().extend([user]))

def createGroup(info,groupName):
    # info contains, list of lists which have name and email
    sObj = Splitwise(consumer_key, secret_key)
    sObj.setAccessToken(session['access_token'])
    group = Group()
    group.setName(groupName)
    users = []
    for data in info:
        newUser = createUser(data[0], data[1], data[2])
        users.append(newUser)
    group.setMembers(users)
    sObj.createGroup(group)

def getExpenses():
    sObj = Splitwise(consumer_key, secret_key)
    sObj.setAccessToken(session['access_token'])
    total_expenses = sObj.getExpenses()
    descriptions = [name.getDescription() for name in total_expenses]
    return descriptions

def transaction(Description, Group, Payer, Price, Contributors):
    # price, date, description, group ID or this particular groups name, members
    sObj = Splitwise(consumer_key, secret_key)
    sObj.setAccessToken(session['access_token'])
    user = sObj.getCurrentUser()
    groups = sObj.getGroups()
    group_dict = {group.getName(): group for group in groups}
    importedData = {'Date': datetime.datetime.now(), 'Description': Description, 'Group': Group, 'Payer': Payer, 'Debit': Price}
    expense = Expense()
    price = float(importedData['Debit'] or 0)
    expense.setCost(price)
    expense.setDate(importedData['Date'])
    expense.setDescription(importedData['Description'])
    expense.setGroupId(group_dict[importedData['Group']].getId())
    members = group_dict[importedData['Group']].getMembers()
    users = []
    contributors = Contributors
    for member in members:
        if member.getFirstName() in contributors:
            user = ExpenseUser()
            user.setId(member.getId())
            if member.getFirstName() == importedData['Payer']:
                user.setPaidShare(price)
            else:
                user.setPaidShare(0)
            users.append(user)
    paid = 0
    share = round(price/len(users), 2)
    for user in users:
        user.setOwedShare(share)
        paid = paid + share
    diff = price - paid
    if diff != 0:
        user = random.choice(users)
        user.setOwedShare(share + diff)
    expense.setUsers(users)
    expense = sObj.createExpense(expense)

@app.errorhandler(500)
def internal_error(error):
	return jsonify(error='An error occurred.')

if __name__ == "__main__":
	app.run(debug=True)