# Matthew Avallone, Beamlak Hailemariam, Allie Haber
# CS3083 Databases
# Pricosha

from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import datetime
from hashlib import sha256

# Initialize the app from Flask
app = Flask(__name__)

# Configure MySQL
conn = pymysql.connect(host='localhost',
                       port=3306,
                       user='root',
                       password='',
                       db='pricosha',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


# Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')


# Define route for login
@app.route('/login')
def login():
    return render_template('login.html')


# Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

# Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    # grabs information from the forms
    email = request.form['email']
    password = request.form['password']
    pw = sha256(password.encode('utf-8')).hexdigest()  # hashed password

    cursor = conn.cursor()
    query = 'SELECT * FROM person WHERE email = %s and password = %s'
    cursor.execute(query, (email, pw))
    data = cursor.fetchone()
    cursor.close()
    error = None
    if data:  # if person has an account
        session['email'] = email  # creates session for person
        return redirect(url_for('home'))
    else:  # returns an error message to the html page
        error = 'Invalid email or password'
        return render_template('login.html', error=error)


# Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    # grabs information from the forms
    fname = request.form['firstName']
    lname = request.form['lastName']
    email = request.form['email']
    password = request.form['password']
    pw = sha256(password.encode('utf-8')).hexdigest()  # hashed password

    cursor = conn.cursor()
    query = 'SELECT * FROM person WHERE email = %s'
    cursor.execute(query, email)
    data = cursor.fetchone()
    error = None
    if data:  # checking to see if person already exists
        error = "This person already exists"
        return render_template('register.html', error=error)
    else:
        ins = 'INSERT INTO person VALUES(%s, %s, %s, %s)'
        cursor.execute(ins, (email, pw, fname, lname))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    email = session['email']
    cursor = conn.cursor()
    #query = 'SELECT item_id, email_post, post_time, file_path, item_name, location FROM contentitem WHERE is_pub = ' \
    #        '1 AND post_time >= NOW() - INTERVAL 1 DAY '  # only show public content posted from the last day
    query = "SELECT item_id, email_post, post_time, file_path, item_name, location FROM contentitem WHERE contentitem.is_pub = 1 "\
            "OR contentitem.email_post= '%s' OR contentitem.item_id in (SELECT item_id FROM share WHERE '%s' in" \
            "(SELECT belong.email FROM belong WHERE share.fg_name = belong.fg_name) OR '%s' in (SELECT owner_email FROM" \
            "friendgroup WHERE share.fg_name = fg_name )) AND post_time >= NOW() - INTERVAL 1 DAY ORDER BY post_time desc"

    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()

    return render_template('home.html', username=email, posts=data)

@app.route('/tagPage')
def tagPage():
    email = session['email']
    cursor = conn.cursor()
    query = 'SELECT item_id, email_tagger, tagtime FROM Tag WHERE email_tagged = %s AND status = %s'
    cursor.execute(query, (email, 'false'))
    data = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor()
    query = 'SELECT item_id, email_tagger, tagtime FROM Tag WHERE email_tagged = %s AND status = %s'
    cursor.execute(query, (email, 'true'))
    data2 = cursor.fetchall()
    cursor.close()

    return render_template('tagPage.html', tagsPending=data, tagsApproved=data2)


@app.route('/logout')
def logout():
    session.pop('email')
    return redirect('/')


@app.route('/addGroup', methods=['POST'])
def addGroup():
    owner_email = session['email']
    fg_name = request.form['group_name']
    description = request.form['description']
    if description == '':  # if description not specified, set it to NULL
        description = None
    cursor = conn.cursor()
    check_created = 'SELECT * FROM FriendGroup WHERE owner_email = %s AND fg_name = %s'
    already_created = cursor.execute(check_created, (owner_email, fg_name))
    cursor.close()
    error = None
    if already_created:
        error = "This group already exists"
        return redirect(url_for('home', error=error))
    else:
        cursor = conn.cursor()
        query1 = 'INSERT INTO FriendGroup(owner_email, fg_name, description) VALUES (%s, %s, %s)'
        query2 = 'INSERT INTO Belong(email, owner_email, fg_name) VALUES (%s, %s, %s)'
        cursor.execute(query1, (owner_email, fg_name, description))
        cursor.execute(query2, (owner_email, owner_email, fg_name))
        conn.commit()
        cursor.close()

    return redirect(url_for('home'))


@app.route('/post', methods=['GET', 'POST'])
def post():
    email = session['email']
    cursor = conn.cursor()
    item_name = request.form['item_name']
    location = request.form['location']
    file_path = request.form['file_path']
    date = datetime.datetime.now()  # fetching the current time (local timezone)
    is_private = request.form['is_private']
    if file_path == '':  # if file_path not specified, set it to NULL
        file_path = None
    if location == '':  # if location not specified, set it to NULL
        location = None

    if is_private == '1':
        is_public = '0'

        friend_group = request.form['friend_group']
        checkFGname = 'SELECT fg_name FROM friendgroup WHERE owner_email = %s AND fg_name = %s'
        cursor.execute(checkFGname, (email, friend_group))  # checking to see if friend group exists in database
        fgname = cursor.fetchone()  # returns tuples of possible friend group names that exist in DB
        cursor.close()

        if fgname:  # if friend group name is valid for specific user, allow group to see content item
            cursor = conn.cursor()
            query = 'INSERT INTO contentItem (email_post, post_time, file_path, item_name, location, is_pub) VALUES(' \
                    '%s, %s, %s, %s, %s, %s) '
            cursor.execute(query, (email, date, file_path, item_name, location, is_public))
            conn.commit()
            cursor.close()

            cursor = conn.cursor()
            getItemID = 'SELECT item_id FROM contentItem WHERE item_name = %s'
            cursor.execute(getItemID, item_name)  # retrieve correct item_id from database to use in next query
            item_id = cursor.fetchone()
            item_id = dict(item_id)  # need to turn tuple into dictionary for easy data access
            cursor.close()

            cursor = conn.cursor()
            addItem2FG = 'INSERT INTO share(owner_email, fg_name, item_id) VALUES(%s, %s, %s)'
            cursor.execute(addItem2FG, (email, friend_group, int(item_id['item_id'])))
            # updating share preferences for friend group

    else:
        is_public = '1'
        query = 'INSERT INTO contentItem (email_post, post_time, file_path, item_name, location, is_pub) VALUES(%s, ' \
                '%s, %s, %s, %s, %s) '
        cursor.execute(query, (email, date, file_path, item_name, location, is_public))

    conn.commit()
    cursor.close()
    return redirect(url_for('home'))


@app.route('/tag', methods=['GET', 'POST'])
def tag():
    cursor = conn.cursor()
    email_tagged = request.form['tagged']
    item_id = request.form['item_id']
    check_tagged = 'SELECT email FROM Person WHERE email = %s'
    cursor.execute(check_tagged, email_tagged)  # checking to see if tagged exists in database
    possible_tagged = cursor.fetchone()  # returns tuples of possible emails to tag that exist in DB
    cursor.close()
    email_tagger = session['email']
    tagtime = datetime.datetime.now()
    cursor = conn.cursor()
    check_duplicate = 'SELECT * FROM Tag WHERE email_tagged = %s AND email_tagger = %s AND item_id =%s'
    duplicate = cursor.execute(check_duplicate, (email_tagged, email_tagger, item_id))
    cursor.close()
    cursor = conn.cursor()
    valid_view = 'SELECT item_id FROM ContentItem WHERE item_id = %s AND (is_pub OR item_id IN (SELECT item_id FROM SHARE JOIN Belong ON SHARE.owner_email = Belong.owner_email AND Share.fg_name = Belong.fg_name WHERE Belong.email = %s))'
    allowed_to_view = cursor.execute(valid_view, (item_id, email_tagged))
    cursor.close()
    error1 = None
    if duplicate:
        print("Hello world")
        error1 = "The tag has already been done"

        return redirect(url_for('home', error=error1))
    else:
        if possible_tagged and allowed_to_view:
            if email_tagged == email_tagger:
                cursor = conn.cursor()
                query = 'INSERT INTO Tag (email_tagged, email_tagger, item_id, status, tagtime) VALUES(%s, %s, %s, %s, %s) '
                cursor.execute(query, (email_tagged, email_tagger, item_id, 'true', tagtime))
            else:
                cursor = conn.cursor()
                query = 'INSERT INTO Tag (email_tagged, email_tagger, item_id, status, tagtime) VALUES(%s, %s, %s, %s, %s) '
                cursor.execute(query, (email_tagged, email_tagger, item_id, 'false', tagtime))
        else:
            error1 = "The person you tagged doesn't exist"
            print("Hello ")
            session
            return redirect(url_for('home', error=error1))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))


@app.route('/tagChoice', methods=['GET', 'POST'])
def tagChoice():
    email_tagged = session['email']
    option = request.form['action']
    email_tagger = request.form['email_tagger']
    item_id = request.form['item_id']
    cursor = conn.cursor()
    if option=="Accept":
        x = True
    elif option=="Decline":
        x = False
    if x:
        query = 'UPDATE Tag SET status = %s WHERE item_id = %s AND email_tagger = %s AND email_tagged = %s'
        cursor.execute(query, ('true', item_id, email_tagger, email_tagged))
        conn.commit()
        cursor.close()
    else:
        cursor = conn.cursor()
        query = 'DELETE FROM Tag WHERE item_id = %s AND email_tagger = %s AND email_tagged = %s'
        cursor.execute(query, (item_id, email_tagger, email_tagged))
        conn.commit()
        cursor.close()
    return redirect(url_for('tagPage'))


app.secret_key = 'some key that you will never guess'
# Run the app on localhost port 5000
# debug = True -> you don't have to restart flask
# for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug=True)
