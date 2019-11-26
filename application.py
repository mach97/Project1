from flask import Flask, render_template,request,session,jsonify,redirect,url_for
from flask_session import Session
import requests
import os
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


app = Flask(__name__)

app.config["SESSION_PERMANENT"]= False
app.config["SESSION_TYPE"]="filesystem"
Session(app)


def api_intern(isbn):
    """ Give all the details about the book"""
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "GiZIkWg77U1CrPFSdJblwQ", "isbns": isbn})
    return res.json()


#print(res.json())

@app.route("/")
def index():
    if not session.get('logged_in'):
        return render_template("index.html")
    else:
        return render_template("books.html")

@app.route("/signin")
def index1():
    if not session.get('logged_in'):
        return render_template("signin.html")
    else:
        return render_template("books.html")

@app.route("/main",methods=["POST"])
def signin():
    #if not session.get('logged_in'):
    #    return render_template("index.html")
    uname = request.form.get("uname")
    name = request.form.get("name")
    lname = request.form.get("lname")
    email = request.form.get("inputEmail")
    password = request.form.get("inputPassword")
    bdate = request.form.get("bdate")

    if db.execute("SELECT username FROM usuario WHERE username=:user",{"user":uname}).rowcount != 0:
        return render_template("error.html", message="Username already exists")
    elif db.execute("SELECT username FROM usuario WHERE email=:user",{"user":email}).rowcount != 0:
        return render_template("error.html", message="Email already exists")
    db.execute("INSERT INTO usuario VALUES (:uname,:name,:lname,:email,:bdate,:password)",{"uname":uname,"name":name,"lname":lname,"email":email,"bdate":bdate,"password":password})
    db.commit()
    return redirect(url_for('index'))

@app.route("/login",methods=["POST","GET"])
def login():
    #if not session.get('logged_in'):
    #    return render_template("index.html")
    uname = request.form.get("uname")
    password = request.form.get("Password")

    if db.execute("SELECT * FROM usuario where username = :uname and password=:password",{"uname":uname,"password":password}).rowcount != 0:
        session['logged_in']=True
        session['user']=uname
        print(session['user'])
        return redirect(url_for('index'))
    else:
        return render_template("error.html",message="Username or Password incorrect")

    if request.method == "GET":
        return render_template("index.html")

@app.route("/logout")
def logout():
    session["logged_in"] = False
    session["user"]=None
    return redirect(url_for('index'))

@app.route("/search",methods=["POST"])
def search():
    text = '%'+request.form.get("search")+'%'
    books = db.execute("SELECT * FROM book WHERE (isbn LIKE :isbn OR title LIKE :title OR author LIKE :author OR year::varchar LIKE :year)", {"isbn":text, "title":text, "author":text, "year":text}).fetchall()
    return render_template("search.html", books=books, search=text)

@app.route("/details/<string:isbn>",methods=["GET","POST"])
def details(isbn):
    isbn, title, author, year, reviews_count, average_rating = db.execute("SELECT isbn, title, author, year, reviews_count, average_rating FROM book WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if average_rating==0 or reviews_count==0:
        book_aux = api_intern(isbn)
        average_rating = book_aux["books"][0]["average_rating"]
        reviews_count = book_aux["books"][0]["reviews_count"]
        db.execute("UPDATE book SET average_rating = :average_rating, reviews_count = :reviews_count WHERE isbn=:isbn", {"isbn": isbn, "average_rating": float(average_rating), "reviews_count": int(reviews_count)})

        db.commit()
    if request.method == "GET":
         return render_template("details.html",isbn=isbn, title=title, author=title, year=year, reviews_count=reviews_count, average_rating=average_rating)
    else:
        return "POST DETAILS"



@app.route("/api/<string:isbn>", methods=["GET"])
def api(isbn):
    """ Give all the details about the book"""
    if request.method == "GET":
        res = db.execute("SELECT title, author, year, isbn, reviews_count, average_rating FROM book WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

        if res is None:
            return render_template("error.html", message="404 book not found", url_return='/', page_name='index'), 404

        title, author, year, isbn, reviews_count, average_rating = res
        if res.reviews_count==0 or res.average_rating==0:
            book_aux = api_intern(isbn)
            average_rating = book_aux["books"][0]["average_rating"]
            reviews_count = book_aux["books"][0]["reviews_count"]

        response = {"title": title, "author": author, "year": year, "isbn": isbn, "review_count": reviews_count, "average_score": average_rating}
        return jsonify(response)


@app.route("/review/<string:isbn>",methods=["GET","POST"])
def review(isbn):
    book = db.execute("SELECT * FROM book WHERE isbn= :isbn", {"isbn": isbn}).fetchone()
    if request.method == "POST":
        review = request.form.get("review")
        score = request.form.get("score")
        average_rating = (book.average_rating + float(score))/2
        reviews_count = book.reviews_count + 1
        comments = db.execute("SELECT * FROM reviews WHERE username= :author_id AND isbn= :book_isbn", {"author_id": session["user"], "book_isbn": isbn}).fetchone()
        if comments is not None:
            return render_template("error.html", message="You already posted a comment to this book")

        db.execute("INSERT INTO reviews(comment, score, username, isbn) VALUES (:review, :score, :author_id, :book_isbn)", {"review": review, "score": score, "author_id": session["user"], "book_isbn": isbn})
        db.execute("UPDATE book SET average_rating = :average_rating, reviews_count = :reviews_count WHERE isbn=:isbn", {"isbn": isbn, "average_rating": average_rating, "reviews_count": reviews_count})

        db.commit()
    reviews = db.execute("SELECT * FROM reviews WHERE isbn= :isbn", {"isbn": isbn}).fetchall()
    return render_template("review.html", book=book, reviews=reviews, isbn=isbn)
