from flask import Flask, request, redirect, render_template, session, flash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:launchcode@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'y337kGcys&zP3B'

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    pub_date = db.Column(db.DateTime)
    body = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, pub_date, owner_id):
        self.title = title
        self.body = body
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date
        self.owner_id = owner_id
    
    def __repr__(self):
        return '<Post %r>' % self.title

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, email, password):
        self.email = email
        self.pw_hash = make_pw_hash(password)

    def __repr__(self):
        return '<Post %r>' % self.email

@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'blog', 'index', 'single_user', 'single']
    if (request.endpoint not in allowed_routes) and 'email' not in session:
        return redirect('/index')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_pw_hash(password, user.pw_hash):
            session['email'] = user.email
            flash("Logged in")
            return redirect('/')
        else:
            flash('User password incorrect, or user does not exist', 'error')
        
    return render_template('login.html', session=False)

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']

        if not is_email(email):
            flash('Zoiks! "' + email + '" does not seem like an email address')
            return redirect('/register')
        # TODO 1: validate that form value of 'verify' matches password
        if matches(email, verify) == True:
            flash('Uh-Oh! Your password and password verification do not match')
            return redirect('/register')
        # TODO 2: validate that there is no user with that email already
        if unique_user(email) == False:
            flash('Uh-Oh! That E-Mail login already exists!')
            return redirect('/register')

        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        session['email'] = user.email
        return redirect("/new-post")
    else:
        return render_template('register.html', session=False)

def unique_user(email):
    if User.query.filter_by(email=email).first():
        return False
    else:
        return True

def matches(email, verify):
    email = email
    verify = verify
    if email == verify:
        return True
    else:
        return False

def is_email(string):
    # for our purposes, an email string has an '@' followed by a '.'
    # there is an embedded language called 'regular expression' that would crunch this implementation down
    # to a one-liner, but we'll keep it simple:
    atsign_index = string.find('@')
    atsign_present = atsign_index >= 0
    if not atsign_present:
        return False
    else:
        domain_dot_index = string.find('.', atsign_index)
        domain_dot_present = domain_dot_index >= 0
        return domain_dot_present
@app.route('/logout')
def logout():
    del session['email']
    return redirect('/')

@app.route('/index')
def index():
    users = User.query.all()
    return render_template('index.html', users=users, session=False)

@app.route('/')
def root():
    if 'email' not in session:
        return redirect('/index')
        
    owner = User.query.filter_by(email=session['email']).first()
    blogs = Blog.query.filter_by(owner=owner).order_by(Blog.pub_date.desc()).all()

    return render_template('blog.html', title="Build-a-Blog!", blogs=blogs, session=True)
    
    
@app.route('/single_user')
def single_user():
    owner_id = request.args.get('id')
    blogs = Blog.query.filter_by(owner_id=owner_id).all()
    return render_template('single_user.html', blogs=blogs, session=False)

@app.route('/blog',  methods=['GET'])
def blog():

    id = request.args.get('id')
    if id:
        blogs = db.session.query(Blog).join(User, Blog.owner_id==User.id)
        email ={}
        for user in User.query.all():
            email[user.id] = user.email
        
        return render_template('blog.html', blogs=blogs, session=False, email=email, author=True)
    
    return render_template('blog.html', session=True)


@app.route('/new-post', methods=['POST', 'GET'])
def new_post():

    if request.method == 'POST':

        title = request.form['title']
        pub_date = datetime.utcnow()
        body = request.form['blog']

        if title =="":
            flash('Please add a title to your blog')
            return redirect('/new-post')
        if body=="":
            flash('Please add content to your blog')
            return redirect('/new-post')

        user = User.query.filter_by(email=session['email']).first()
        owner_id = user.id
        new_blog = Blog(title=title, body=body, pub_date=pub_date, owner_id=owner_id)
        db.session.add(new_blog)
        db.session.commit()
        return redirect('/single?id=' + str(new_blog.id))


    return render_template('new-post.html', session=True)

@app.route('/single', methods=['POST', 'GET'])
def single():
    id = request.args.get('id')
    blog = Blog.query.get(id)
    email ={}
    for user in User.query.all():
        email[user.id] = user.email
    return render_template('single.html', blog=blog, email=email, session=True)

if __name__ == '__main__':
    app.run()