import os

from flask import Flask, render_template, jsonify, request, flash, session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_session import Session


app = Flask(__name__)

app.secret_key = os.urandom(12)


# DB example
# export DATABASE_URL = "postgres://user:password@address:port/database"

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def registration_form_info_is_correct(name, lastname, username, password, password_confirmation, avatar):
    if name.isspace() or lastname.isspace() or username.isspace() or password.isspace():
        render_template("error.html", message="Please make sure to provide all the information and try again")
        return False
   
    if not Database.check_if_username_is_available(username):
        render_template("error.html", message="username not available, try again")
        return False

    if password != password_confirmation:
        button = 1
        render_template("error.html", message="Password confirmation doesn't match", button_1=button)
        return False

    if avatar == '':
        render_template("error.html", message="Please choose an avatar")
        return False
    
    return True

def generate_rate_dict(books_list):
    rate_dict = {}

    for book in books_list:
        rate = Database.calculate_avg_rating(book.id)
        if rate != None:
            half_star = float(rate)%1
            if half_star > 0:
                rate_dict[book.id] = (int(rate), 1)
            else:
                rate_dict[book.id] = (int(rate), 0)
        else:
            rate_dict[book.id] = (0,0)
            
    return rate_dict


class Database():

    @staticmethod
    def select_all_users():
        return db.execute("select * from users")

    @staticmethod
    def select_username_password(username, password):
       return db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()

    @staticmethod
    def insert_into_users(name, lastname, password, username, avatar):
            db.execute("INSERT INTO users (first_name, last_name, pw, username, avatar) VALUES (:fname, :lname, :pw, :username, :avatar)",
                {"fname":name, "lname": lastname, "pw": password, "username":username, "avatar":avatar})
            db.commit()
    
    @staticmethod
    def check_if_username_is_available(username):
        return db.execute("SELECT * FROM users WHERE username=:username", {"username": username}).rowcount == 0

    @staticmethod
    def insert_into_reviews(user_id, review, rate, book_id):
        db.execute("INSERT INTO reviews (user_id, review, rate, book_id) VALUES (:user_id, :review, :rate, :book_id)",
                    {"user_id":user_id, "review": review, "rate": rate, "book_id":book_id})
        db.commit()

    @staticmethod
    def select_reviews(book_id):
        reviews = db.execute(f"SELECT * FROM reviews WHERE book_id='{book_id}'").fetchall()
        return reviews

    @staticmethod
    def get_users_info(reviews):
        user_info = {}
        for review in reviews:    
            user = db.execute(f"SELECT * FROM users WHERE id='{review.user_id}'").fetchone()
            user_info[review.user_id] = user
            
        return user_info
    @staticmethod
    def get_profile_info(user_id):
        return db.execute(f"SELECT * FROM users WHERE id='{user_id}'").fetchone()

    @staticmethod
    def select_best_books(avg_review=4.5):
        return db.execute(f"select * from books where goodreads_avg_review>{avg_review} order by goodreads_avg_review desc;").fetchall()

    @staticmethod
    def select_all_books():
        return db.execute("select * from books order by title").fetchall()
    
    @staticmethod
    def search_all_books_with(search_content):
        where = ['author', 'title', 'isbn']
        result = []
        for query_name in where:
            sql = f"SELECT * FROM books WHERE lower({query_name}) Like lower('%{search_content}%')"
            books = db.execute(sql).fetchall()
            for book in books:
                result.append(book)
        return result

    @staticmethod
    def select_book_by_id(book_id):
        return db.execute("SELECT * FROM books WHERE id= :id", {"id": book_id}).fetchone()

    @staticmethod
    def select_book_by_isbn(book_isbn):
        print("search by book_isbn", book_isbn)
        return db.execute(f"SELECT * FROM books WHERE isbn= :isbn", {"isbn": book_isbn}).fetchone()

    @staticmethod
    def select_review_by_user_id_and_book_id(user_id, book_id):
        return db.execute(f"select * from reviews where book_id ={book_id} and user_id={user_id}").rowcount > 0


    @staticmethod
    def calculate_avg_rating(book_id):
        rate = db.execute(f"SELECT AVG(rate) FROM reviews WHERE book_id={book_id};").fetchone()[0]
        return rate
    
    @staticmethod
    def get_review_count(book_id):
        return db.execute(f"SELECT COUNT(*) FROM reviews WHERE book_id={book_id}").fetchone()[0]
   

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/success", methods=["POST"])
def register():
    name = request.form.get("name")
    lastname = request.form.get("lname")
    username = request.form.get("username")
    password = request.form.get("password")
    password_confirmation = request.form.get("password_confirmation")
    avatar = request.form.get("avatar")

    if registration_form_info_is_correct(name, lastname, username, password, password_confirmation, avatar):
        Database.insert_into_users(name, lastname, password, username, avatar)
        return render_template("index.html")
    else:
        return render_template("error.html", message="provide correct info")


@app.route("/welcome", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    
    user_info = Database.select_username_password(username, password)

    if user_info != None:
        if password == user_info.pw:

            session['user_id'] = user_info.id
            books_list = Database.select_best_books()
            rate_dict = generate_rate_dict(books_list)
            
            return render_template("home.html", books_list=books_list, rate_dict=rate_dict, pagetitle="Best Books")
        else:
            return render_template("error.html", message="Wrong password.")    
    else:    
        return render_template("error.html", message="You are not a member")

@app.route("/profile")
def profile():
    if session.get('user_id'):
        profile_info = Database.get_profile_info(session['user_id'])
        print(profile_info)
        return render_template('profile_page.html', user_info=profile_info)
    else:
        pass


@app.route("/logout")
def logout():
    if session.get('user_id'):
        del session['user_id']
        return render_template('index.html')
    else:
        pass

@app.route("/search-result",methods=["POST"])
def search():
    search_content = request.form.get("search")

    result = Database.search_all_books_with(search_content)
    
    if len(result) == 0:
        pagetitle = "Sorry, book not found"
    else:
        pagetitle = f" Result for '{search_content}'"
    
    rate_dict = generate_rate_dict(result)

    return render_template("home.html", books_list=result, rate_dict=rate_dict, pagetitle=pagetitle)


@app.route("/all-books")
def all_books():
    all_books_list = Database.select_all_books()
   
    rate_dict = generate_rate_dict(all_books_list)

    return render_template("home.html", books_list=all_books_list, rate_dict=rate_dict, pagetitle="All Books A-Z")

@app.route("/all-books/<int:book_id>")
def more(book_id):

    book = Database.select_book_by_id(book_id)
    
    if book is None:
        return render_template("error.html", message="book not found, sorry")
    else:
        reviews_list = Database.select_reviews(book_id)
        user_info = Database.get_users_info(reviews_list)
        

        return render_template("book.html", book=book, reviews_list=reviews_list, user_info=user_info, pagetitle="Reviews from others")


@app.route("/submited/<int:book_id>", methods=["POST"])
def submit_review(book_id):
    review = request.form.get("review")
    rate = request.form.get("rate")
    print(review)
    print("user info: ", session['user_id'])

    rowcount = Database.select_review_by_user_id_and_book_id(session['user_id'], book_id)
    
    if review.isspace():
        return render_template("error.html", message="Please, write a review")
    if rowcount:
        return render_template("error.html", message="You already posted a review about that book.")

    else:
        Database.insert_into_reviews(session['user_id'], review, rate, book_id)
        all_books_list = Database.select_all_books()
        rate_dict = generate_rate_dict(all_books_list)

        return render_template("home.html", books_list=all_books_list, rate_dict=rate_dict, pagetitle="All Books A-Z")

@app.route("/api/<book_isbn>")
def book_api(book_isbn):

    book = Database.select_book_by_isbn(book_isbn)
  
    if book is None:
        return jsonify({"error":"invalid isbn"}), 422

    review_count = Database.get_review_count(book.id)
    average_score = int(Database.calculate_avg_rating(book.id))

    return jsonify({
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "isbn": book.isbn,
            "review_count": review_count,
            "average_score": average_score
            })
