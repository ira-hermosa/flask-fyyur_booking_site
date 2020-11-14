#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from models import *
import json
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate


#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://ira:ira@localhost:5432/fyyur'
db = SQLAlchemy(app)

migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

from models import *

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


# ---------------------------------------------------------------------------#
# Venues
# ---------------------------------------------------------------------------#


# Get request for venues. 
# Number of shows is an aggregate of upcominghows per venue.
@app.route('/venues')
def venues():

    data = []
    locations = db.session.query(Venue.city, Venue.state).distinct()

    for location in locations:
        location_venues = Venue.query.filter_by(
            state=location.state).filter_by(
            city=location.city).all()
        venue_data = []

        for venue in location_venues:
            venue_data.append({"id": venue.id, "name": venue.name, "num_upcoming_show": len(
                Show.query.filter(Show.venue_id == 1).filter(Show.start_time > datetime.now()).all())})

        data.append({
            "city": location.city,
            "state": location.state,
            "venues": venue_data
        })

    return render_template('pages/venues.html', areas=data)


# Get request for searching venues with partial string search. 
# Search is case-insensitive
@app.route('/venues/search', methods=['POST'])
def search_venues():

    search_term = request.form.get('search_term', '')
    result = Venue.query.filter(Venue.name.ilike(f'%{search_term}%'))

    response = {
        "count": result.count(),
        "data": result
    }
    return render_template(
        'pages/search_venues.html',
        results=response,
        search_term=search_term)


# Get request for venues by venue id
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    venue = Venue.query.get(venue_id)

    upcoming_shows_all = Show.query.join(Artist).filter(
        Show.venue_id == venue_id).filter(
        Show.start_time > datetime.now()).all()
    upcoming_shows = []

    past_shows_all = Show.query.join(Artist).filter(
        Show.venue_id == venue_id).filter(
        Show.start_time < datetime.now()).all()
    past_shows = []

    for show in past_shows_all:
        past_shows.append(
            {
                "artist_id": show.artist_id,
                "artist_name": db.session.query(
                    Artist.name).filter_by(
                    id=show.artist_id).first()[0],
                "artist_image_link": db.session.query(
                    Artist.image_link).filter_by(
                        id=show.artist_id).first()[0],
                "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')})

    for show in upcoming_shows_all:
        upcoming_shows.append(
            {
                "artist_id": show.artist_id,
                "artist_name": db.session.query(
                    Artist.name).filter_by(
                    id=show.artist_id).first()[0],
                "artist_image_link": db.session.query(
                    Artist.image_link).filter_by(
                        id=show.artist_id).first()[0],
                "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")})

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_venue.html', venue=data)


# Get request to render form template on the client
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


# Creates a venue record in the db using form data.
@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

    try:
        venue_name = request.form.get('name', '')
        venue_city = request.form.get('city', '')
        venue_state = request.form.get('state', '')
        venue_phone = request.form.get('phone', '')
        venue_address = request.form.get('address', '')
        venue_website = request.form.get('website', '')
        venue_genres = request.form.getlist('genres')
        venue_facebooklink = request.form.get('facebook_link', '')
        venue_imagelink = request.form.get('image_link', '')
        if request.form.get('seeking_talent'):
            venue_seekingtalent = True
        else:
            venue_seekingtalent = False
        venue_seekingdescription = request.form.get('seeking_description', '')
        venue = Venue(
            name=venue_name,
            image_link=venue_imagelink,
            seeking_talent=venue_seekingtalent,
            seeking_description=venue_seekingdescription,
            city=venue_city,
            state=venue_state,
            phone=venue_phone,
            address=venue_address,
            genres=venue_genres,
            facebook_link=venue_facebooklink,
            website=venue_website)
        db.session.add(venue)
        db.session.commit()

# on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')

# on unsuccessful db insert, flash an error instead.
    except BaseException:
        db.session.rollback()
        flash(
            'An error occurred. Venue ' +
            request.form['name'] +
            ' could not be listed.')

    finally:
        db.session.close()

    return render_template('pages/home.html')


# Deletes a venue record by venue id in the db
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

    try:
        venue = db.session.query(Venue).filter(Venue.id)
        venue_name = venue.name

        db.session.delete(venue)
        db.session.commit()

        flash('Venue' + venue_name + ' was deleted')

    except BaseException:
        db.session.rollback()
        flash('An error ocuured. Venue' + venue_name + 'could not be deleted')

    finally:
        db.session.close()

    return redirect(url_for('index'))

    return None


# Updates an existing venue record with venue id
@app.route('/venues/<int:venue_id>/edit', methods=['PATCH'])
def edit_venue_submission(venue_id):

    form = VenueForm()
    venue = Venue.query.get(venue_id)

    try:
        venue.name = request.form.get['name']
        venue.city = request.form.get['city']
        venue.state = request.form.get['state']
        venue.address = request.form.get['address']
        venue.phone = request.form.get['phone']
        venue.genres = request.form.getlist('genres')
        venue.image_link = request.form.get['image_link']
        venue.facebook_link = request.form.get['facebook_link']
        venue.website = request.form.get['website']
        venue.seeking_talent = True if 'seeking_talent' in request.form.get else False
        venue.seeking_description = request.form['seeking_description']

        db.session.commit()
        flask('Venue' + request.form['name'] + 'has been updated')

    except BaseException:
        db.session.rollback()
        flash('An error has occured. Venue has not been updated')

    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))


# Gets venue details for a venue record in the db
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

    form = VenueForm()
    venue = Artist.query.get(venue_id)

    if venue:
        form.name.data = venue.name
        form.city.data = venue.city
        form.state.data = venue.state
        form.phone.data = venue.phone
        form.address.data = venue.address
        form.genres.data = venue.genres
        form.facebook_link.data = venue.facebook_link
        form.image_link.data = venue.image_link
        form.website.data = venue.website
        form.seeking_talent.data = venue.seeking_talent
        form.seeking_description.data = venue.seeking_description

    return render_template('forms/edit_venue.html', form=form, venue=venue)


# ----------------------------------------------------------------#
#  Artists
# ----------------------------------------------------------------#

# Gets request for all artists in the db
@app.route('/artists')
def artists():

    data = []
    artists = db.session.query(Artist).all()

    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name
        })
    return render_template('pages/artists.html', artists=data)


# Gets request for searching an artist with partial string search. 
# Search is case-insensitive
@app.route('/artists/search', methods=['POST'])
def search_artists():

    search_term = request.form.get('search_term', '')
    result = Artist.query.filter(Artist.name.ilike(f'%{search_term}%'))

    response = {
        "count": result.count(),
        "data": result
    }
    return render_template(
        'pages/search_artists.html',
        results=response,
        search_term=request.form.get(
            'search_term',
            ''))


# Gets request to render artist form
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


# Creates a new artist record in the db using form
@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

    try:
        artist_name = request.form.get('name', '')
        artist_city = request.form.get('city', '')
        artist_state = request.form.get('state', '')
        artist_phone = request.form.get('phone', '')
        artist_website = request.form.get('website', '')
        artist_genres = request.form.getlist('genres')
        artist_facebooklink = request.form.get('facebook_link', '')
        artist_imagelink = request.form.get('image_link', '')
        if request.form.get('seeking_venue'):
            artist_seekingvenue = True
        else:
            artist_seekingvenue = False
        artist_seekingdescription = request.form.get('seeking_description', '')
        artist = Artist(
            name=artist_name,
            image_link=artist_imagelink,
            seeking_venue=artist_seekingvenue,
            seeking_description=artist_seekingdescription,
            city=artist_city,
            state=artist_state,
            phone=artist_phone,
            website=artist_website,
            genres=artist_genres,
            facebook_link=artist_facebooklink)
        db.session.add(artist)
        db.session.commit()

# on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')

# on unsuccessful db insert, flash an error instead.
    except BaseException:
        db.session.rollback()
        flash(
            'An error occurred. Artist ' +
            request.form['name'] +
            ' could not be listed.')

    finally:
        db.session.close()

    return render_template('pages/home.html')


# Get request for past and upcoming shows of an artist in the db.
# Past and incoming shows specify the relevant venues.
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    artist = Artist.query.get(artist_id)

    upcoming_shows_all = Show.query.join(Venue).filter(
        Show.artist_id == artist_id).filter(
        Show.start_time > datetime.now()).all()
    upcoming_shows = []

    past_shows_all = Show.query.join(Venue).filter(
        Show.artist_id == artist_id).filter(
        Show.start_time < datetime.now()).all()
    past_shows = []

    for show in past_shows_all:
        past_shows.append(
            {
                "venue_id": show.venue_id,
                "venue_name": db.session.query(
                    Venue.name).filter_by(
                    id=show.venue_id).first()[0],
                "venue_image_link": db.session.query(
                    Venue.image_link).filter_by(
                        id=show.venue_id).first()[0],
                "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')})

    for show in upcoming_shows_all:
        upcoming_shows.append(
            {
                "venue_id": show.venue_id,
                "venue_name": db.session.query(
                    Venue.name).filter_by(
                    id=show.venue_id).first()[0],
                "venue_image_link": db.session.query(
                    Venue.image_link).filter_by(
                        id=show.venue_id).first()[0],
                "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")})

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "facebook_link": artist.facebook_link,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
    }

    return render_template('pages/show_artist.html', artist=data)


# Gets details of an artist record in the db
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    if artist:
        form.name.data = artist.name
        form.city.data = artist.city
        form.state.data = artist.state
        form.genres.data = artist.genres
        form.phone.data = artist.phone
        form.website.data = artist.website
        form.facebook_link.data = artist.facebook_link
        form.seeking_venue = artist.seeking_venue
        form.seeking_description = artist.seeking_description
        form.image_link = artist.image_link

    return render_template('forms/edit_artist.html', form=form, artist=artist)


# Updates an existing artist record with artist id using new attributes
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    try:
        artist.name = request.form.get['name']
        artist.city = request.form.get['city']
        artist.state = request.form.get['state']
        artist.phone = request.form.get['phone']
        artist.genres = request.form.getlist('genres')
        artist.image_link = request.form.get['image_link']
        artist.facebook_link = request.form.get['facebook_link']
        artist.website = request.form.get['website']
        artist.seeking_venue = True if 'seeking_venue' in request.form.get else False
        artist.seeking_description = request.form['seeking_description']

        db.session.commit()
        flash(
            'Artist' +
            request.form['name'] +
            'has been successfully updated.')

    except BaseException:
        db.session.rollback()
        flash('An error has occured and the update is unsuccessful')

    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


# -----------------------------------------------------------------#
#  Shows
# -----------------------------------------------------------------#

# Gets all show records in the db comprising relevant venue details, artist details and start time
@app.route('/shows')
def shows():

    # shows = Show.query.all()
    shows = db.session.query(Show).all()
    data = []
    for show in shows:
        show = {
            "venue_id": show.venue_id,
            "venue_name": db.session.query(
                Venue.name).filter_by(
                id=show.venue_id).first()[0],
            "artist_id": show.artist_id,
            "artist_name": db.session.query(
                Artist.name).filter_by(
                    id=show.artist_id).first()[0],
            "artist_image_link": db.session.query(
                        Artist.image_link).filter_by(
                            id=show.artist_id).first()[0],
            "start_time": format_datetime(
                                str(
                                    show.start_time))}
        data.append(show)

    return render_template('pages/shows.html', shows=data)


# Render shows form
@app.route('/shows/create')
def create_shows():

    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


# Create a new show in db using form data
@app.route('/shows/create', methods=['POST'])
def create_show_submission():

    try:
        show_venue = request.form.get('venue_id', '')
        show_artist = request.form.get('artist_id', '')
        show_starttime = request.form.get('start_time', '')
        show = Show(
            venue_id=show_venue,
            artist_id=show_artist,
            start_time=show_starttime)
        db.session.add(show)
        db.session.commit()

# on successful db insert, flash success
        flash(
            'Show at' +
            request.form['venue_id'] +
            'was successfully listed!')

# on unsuccessful db insert, flash an error instead.
    except BaseException:
        db.session.rollback()
        flash(
            'An error occurred. Show at' +
            request.form['venue_id'] +
            ' could not be listed.')

    finally:
        db.session.close()

    return render_template('pages/home.html')


#-------------------------------------------------------------------------#
# Error handlers
#-------------------------------------------------------------------------#

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')


#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
