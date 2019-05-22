from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)

#configuration for MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'MyNewPass123'
app.config['MYSQL_DB'] = 'myfirstflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#to initialize the database
mysql = MySQL(app)



#homepage route
@app.route('/')
def index():
        return render_template('home.html')

#about page route
@app.route('/about')
def about():
        return render_template('about.html')

#blog page route
@app.route('/blogs')
def blogs():
        #Create cursor
        cur = mysql.connection.cursor()

        #Get Blog Post
        result = cur.execute("SELECT * FROM blogs")
        blogs = cur.fetchall()

        if result > 0:
                return render_template('blogs.html', blogs = blogs)
        else:
                msg = 'No Blog Post Found!'
                return render_template('blogs.html', msg = msg)
        #Close Connection
        cur.close()


@app.route('/blog/<string:id>/')
def blog(id):
        #Create cursor
        cur = mysql.connection.cursor()

        #Get Blog Post
        result = cur.execute("SELECT * FROM blogs WHERE id = %s", [id])
        blog = cur.fetchone()
        return render_template('blog.html', blog=blog)

#class for register form
class RegisterForm(Form):
        name = StringField('Name', [validators.Length(min = 1, max = 50)])
        username = StringField ('Username', [validators.Length(min = 4, max = 25)])
        email = StringField ('Email', [validators.Length(min = 4, max = 50)])
        password = PasswordField('Password',[validators.DataRequired(),validators.EqualTo('confirm' , message = "Password Mismatch!")])
        confirm = PasswordField("Confirm Password")

#register route
@app.route('/register', methods = ['GET', 'POST'])
def register():
        form = RegisterForm(request.form)
        if request.method == 'POST' and form.validate():
                name = form.name.data
                email = form.email.data
                username = form.username.data
                password = sha256_crypt.encrypt(str(form.password.data))

                #to create cursor
                cur = mysql.connection.cursor()
                
                cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

                #commit to DB
                mysql.connection.commit()

                #close connection
                cur.close()

                flash('Registration complete. You can now log in.', 'success' )

                return redirect(url_for('login'))
        return render_template('register.html', form = form)

#For User Login
@app.route('/login', methods = ['GET', 'POST'])
def login():
        if request.method == 'POST':
                #GET FORM Field
                username = request.form['username']
                password_candidate = request.form['password']

                #create cursor

                cur = mysql.connection.cursor()

                #get user by username
                result = cur.execute('SELECT * FROM users WHERE username = %s', [username])

                if result > 0:
                        #Get stored hash
                        data = cur.fetchone()
                        password = data['password']

                        #comparing password

                        if sha256_crypt.verify(password_candidate, password):
                                #if passed
                                session['logged_in'] = True
                                session['username'] = username

                                flash('You are logged in', 'success')
                                return redirect(url_for('dashboard'))
                        else:
                                error = 'Invalid Login'
                                return render_template('login.html', error=error)
                                #close connection
                                cur.close()
                else:
                        error = 'Username not found'
                        return render_template('login.html', error=error)

        return render_template('login.html')

#to check if user is logged in
def is_logged_in(f):
        @wraps(f)
        def wrap(*args, **kwargs):
                if 'logged_in' in session:
                        return f(*args, **kwargs)
                else:
                        flash('Unauthorized! Please login.', 'danger')
                        return redirect(url_for('login'))
        return wrap

#logout route
@app.route('/logout')
@is_logged_in
def logout():
        session.clear()
        flash('Logged out', 'success')
        return redirect(url_for('login'))

#dashboard page route
@app.route('/dashboard')
@is_logged_in
def dashboard():
        #Create cursor
        cur = mysql.connection.cursor()

        #Get Blog Post
        result = cur.execute("SELECT * FROM blogs")
        blogs = cur.fetchall()

        if result > 0:
                return render_template('dashboard.html', blogs = blogs)
        else:
                msg = 'No Blog Post Found!'
                return render_template('dashboard.html', msg = msg)
        #Close Connection
        cur.close()
        

#class for blog post form
class BlogForm(Form):
        title = StringField('Title', [validators.Length(min = 1, max = 200)])
        body = TextAreaField ('Body', [validators.Length(min = 30)])

#add blog post route
@app.route('/add_blog_post', methods = ['GET', 'POST'])
@is_logged_in
def add_blog_post():
        form = BlogForm(request.form)
        if request.method == 'POST' and form.validate():
                title = form.title.data
                body = form.body.data

                #Create Cursor
                cur = mysql.connection.cursor()

                #Execute Query
                cur.execute("INSERT INTO blogs(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))

                #commit to DB
                mysql.connection.commit()

                #close connection
                cur.close()

                flash('Blog Post Created', 'success')
                return redirect(url_for('dashboard'))
        return render_template('add_blog_post.html', form=form)
        
#edit blog post route
@app.route('/edit_blog_post/<string:id>', methods = ['GET', 'POST'])
@is_logged_in
def edit_blog_post(id):
        #Create Cursor
        cur = mysql.connection.cursor()

        #Get Blog post by id
        result = cur.execute("SELECT * from blogs WHERE id = %s", [id])
        blog = cur.fetchone()

        #GET from
        form = BlogForm(request.form)

        #populate blog form fields
        form.title.data = blog['title']
        form.body.data = blog['body']

        if request.method == 'POST' and form.validate():
                title = request.form['title']
                body = request.form['body']

                #Create Cursor
                cur = mysql.connection.cursor()

                #Execute Query
                cur.execute("UPDATE blogs SET title = %s, body = %s WHERE id=%s", (title, body, id))
                #commit to DB
                mysql.connection.commit()

                #close connection
                cur.close()

                flash('Blog Post Updated', 'success')
                return redirect(url_for('dashboard'))
        return render_template('edit_blog_post.html', form=form)

#Delete Blog
@app.route('/delete_blog/<string:id>', methods = ['POST'])
@is_logged_in
def delete_blog(id):
        cur = mysql.connection.cursor

        cur.execute("DELETE FROM articles WHERE id = %s", [id])

        #commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()
        flash('Blog Post Deleted', 'success')
        return redirect(url_for('dashboard'))




if __name__ == '__main__':
    app.secret_key = 'uniquekey123'    
    app.run(debug = True, port = 5000)