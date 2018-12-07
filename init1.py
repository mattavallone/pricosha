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
    cursor = conn.cursor()
    query = 'SELECT item_id, email_post, post_time, file_path, item_name, location FROM contentitem WHERE is_pub = ' \
            '1 AND post_time >= NOW() - INTERVAL 1 DAY '  # only show public content posted from the last day
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('index.html', publicposts=data)


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
    query = 'SELECT item_id, email_post, post_time, file_path, item_name, location FROM contentitem WHERE is_pub = ' \
            '1 AND post_time >= NOW() - INTERVAL 1 DAY '  # only show public content posted from the last day
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()

    cursor = conn.cursor()
    fgnames = 'SELECT fg_name FROM friendgroup WHERE owner_email = %s'
    cursor.execute(fgnames, email)  # retrieving friend groups existing in database
    fg = cursor.fetchall()  # returns tuples of possible friend group names that exist in DB
    cursor.close()

    cursor = conn.cursor()
    comments = 'SELECT commenter, item_id, comment FROM comment WHERE commenter = %s AND is_public = 1'
    cursor.execute(comments, email)  # retrieving friend groups existing in database
    cm = cursor.fetchall()  # returns tuples of possible friend group names that exist in DB
    cursor.close()

    cursor = conn.cursor()
    createFGview = 'CREATE VIEW FG AS (SELECT fg_name FROM belong WHERE belong.email = %s); '
    cursor.execute(createFGview, email)
    conn.commit()
    locdata = 'SELECT location, email_post AS Email FROM contentItem WHERE location IS NOT NULL AND ' \
              'contentItem.email_post IN (SELECT DISTINCT email FROM belong NATURAL JOIN FG WHERE email != %s)AND ' \
              'location IN (SELECT DISTINCT location FROM contentItem WHERE email_post = %s); '
    cursor.execute(locdata, (email,email))
    loc = cursor.fetchall()
    dropFGview = 'DROP VIEW FG;'
    cursor.execute(dropFGview)
    conn.commit()
    cursor.close()
    return render_template('home.html', username=email, posts=data, fg=fg, locdata=loc, comments = cm)


@app.route('/logout')
def logout():
    session.pop('email')
    return redirect('/')


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

        friend_group = request.form.getlist('friend_group')

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

        cursor = conn.cursor()  # updating share preferences for friend group
        addItem2FG = 'INSERT INTO share(owner_email, fg_name, item_id) VALUES(%s, %s, %s)'
        for fg_name in friend_group:
            cursor.execute(addItem2FG, (email, fg_name, int(item_id['item_id'])))
            conn.commit()

    else:
        is_public = '1'
        query = 'INSERT INTO contentItem (email_post, post_time, file_path, item_name, location, is_pub) VALUES(%s, ' \
                '%s, %s, %s, %s, %s) '
        cursor.execute(query, (email, date, file_path, item_name, location, is_public))
        conn.commit()

    cursor.close()
    return redirect(url_for('home'))


@app.route('/comment', methods=['GET', 'POST'])
def comment():
    email = session['email']
    cursor = conn.cursor()
    com = request.form['comment']
    content_id = request.form['content_ids']
    is_pub = request.form['is_public']
    addComment = 'INSERT INTO comment(commenter, item_id, comment, is_public) VALUES(%s, %s, %s, %s)'
    cursor.execute(addComment, (email, content_id, com, is_pub))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))


app.secret_key = 'some key that you will never guess'
# Run the app on localhost port 5000
# debug = True -> you don't have to restart flask
# for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug=True)
