from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests


class UpdateRatingForm(FlaskForm):
    rating = StringField(label="Your Rating Out of 10 e.g. 7.5 :", validators=[DataRequired()])
    review = StringField(label="Your Review:", validators=[DataRequired()])
    submit = SubmitField(label="Done")


class AddMovieForm(FlaskForm):
    title = StringField(label="Movie Title:", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")


app = Flask(__name__)
app.config['SECRET_KEY'] = ''
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top-movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = ""
db = SQLAlchemy(app)
Bootstrap(app)


class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f"<Movie Title: {self.title}>"


db.create_all()

# new_movie = Movies(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# db.session.add(new_movie)
# db.session.commit()


@app.route("/")
def home():
    movies = Movies.query.order_by(Movies.rating).all()
    # print(movies)
    for n in range(len(movies)):
        movies[n].ranking = len(movies) - n
    db.session.commit()
    return render_template("index.html", all_movies=movies)


@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    rating_form = UpdateRatingForm()
    movie_id = request.args.get("movie_id")
    movie_to_update = Movies.query.get(movie_id)

    if rating_form.validate_on_submit():
        movie_to_update.rating = float(rating_form.rating.data)
        movie_to_update.review = rating_form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=rating_form, movie=movie_to_update)


@app.route("/del")
def delete_movie():
    movie_id = request.args.get("movie_id")
    movie_to_delete = Movies.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    add_movie_form = AddMovieForm()

    if add_movie_form.validate_on_submit():
        # print(add_movie_form.title.data)

        tmdb_api_key = ""
        tmdb_url = "https://api.themoviedb.org/3/search/movie"
        parameters = {"api_key": tmdb_api_key,
                      "query": add_movie_form.title.data
                      }
        search_query = requests.get(url=tmdb_url, params=parameters).json()["results"]
        # print(search_query)

        return render_template("select.html", search_query=search_query)
    return render_template("add.html", form=add_movie_form)


@app.route("/select")
def select():
    tmdb_movie_id = request.args.get("tmdb_movie_id")
    tmdb_api_key = ""
    tmdb_url = f"https://api.themoviedb.org/3/movie/{tmdb_movie_id}?api_key={tmdb_api_key}&language=en-US"

    search_query = requests.get(url=tmdb_url).json()
    # print(search_query)

    new_movie = Movies(title=search_query["title"],
                       year=search_query["release_date"].split("-")[0],
                       description=search_query["overview"],
                       img_url=f"https://image.tmdb.org/t/p/w500{search_query['poster_path']}")
    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for("rate_movie", movie_id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
