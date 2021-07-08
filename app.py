#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import *
import config
from flask_migrate import Migrate
from sqlalchemy.sql.sqltypes import Boolean

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#**********************************************************************************************************
#                                               VENUES
#**********************************************************************************************************

#------------------------------DISPLAYING VENUES--------------------------
@app.route('/venues')
def venues():
  data = []

  #reading venues from the database
  venues = Venue.query.all()

  #group venues that have the same city and state
  locations = set()
  for venue in venues:
    locations.add((venue.city, venue.state))

  for location in locations: 
    data.append({
      "city": location[0],
      "state": location[1],
      "venues": []
    })

  for venue in venues:
    num_upcoming_shows = 0
    shows = Show.query.filter_by(venue_id=venue.id).all()

    # filtering num_shows
    current_date = datetime.now()  

    for show in shows:
      if show.start_time > current_date:
        num_upcoming_shows += 1
    

    for venue_location in data:
      if venue.state == venue_location['state'] and venue.city == venue_location['city']:
        venue_location['venues'].append({
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": num_upcoming_shows
        })

  return render_template('pages/venues.html', areas=data)

#---------------------------SEARCHING FOR A VENUE-----------------------
@app.route('/venues/search', methods=['POST'])
def search_venues():
  #search allows partial string matching and case-insentive
  search_term = request.form.get('search_term', '')
  search_result = Venue.query.filter(Venue.name.ilike(f'%{search_term}%'))
  response={
    "count": search_result.count(),
    "data": search_result
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))
  

#------------------------DISPLAYING A VENUE'S DATA-----------------------
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  #Using of JOIN queries to get past and upcoming shows
  #upcoming shows > current time, past shows < current time
  past_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
  past_shows = []
  upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows = []

  #displaying past and upcoming shows for the displayed venue
  for show in past_shows_query:
    past_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  for show in upcoming_shows_query:
    upcoming_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")    
    })

  #displaying data of displayed venue
  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website_link": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_num": len(past_shows),
    "upcoming_shows_num": len(upcoming_shows)
  }

  return render_template('pages/show_venue.html', venue=data)

#-----------------------------CREATE A VENUE------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form)
  try:
    venue = Venue(
      name=form.name.data,
      city=form.city.data,
      state=form.state.data,
      address=form.address.data,
      phone=form.phone.data,
      genres=form.genres.data,
      image_link=form.image_link.data,
      facebook_link=form.facebook_link.data,
      website_link=form.website_link.data,
      seeking_talent=form.seeking_talent.data,
      seeking_description=form.seeking_description.data
    )
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue '+ request.form['name'] + ' could not be listed')
  finally:
    db.session.close()
 
  return render_template('pages/home.html')

#--------------------------DELETING A VENUE------------------
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    venue_name = venue.name
    db.session.delete(venue)
    db.session.commit()
    #On successice deletion, show a message that venue was deleted
    flash('Venue ' + venue_name + ' was deleted')
  except:
    #In case of failures, show a message that an error occured
    flash(' an error occured and Venue ' + venue_name + ' was not deleted')
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('index'))

#------------------------EDITING & UPDATING VENUE-------------------
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  venue={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website_link": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
  }
  return render_template('forms/edit_venue.html', form=form, venue=venue)

#-------------------------EDIT VENUES SUBMISSION FORM-------------------------
@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    form = VenueForm(request.form)
    venue = Venue.query.get(venue_id)

    venue.name = form.name.data
    venue.genres = form.genres.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    venue.facebook_link = form.facebook_link.data
    venue.website_link = form.website_link.data
    venue.image_link = form.image_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data

    db.session.commit()
    #Succesice update
    flash('Venue ' + request.form['name'] + 'has been updated')
  except:
    #Failure of updating
    db.session.rollback()
    flash('An error occured while trying to update Venue')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))
  
#*****************************************************************************************************
#                                                ARTISTS
#*****************************************************************************************************

#-------------DISPLAY ARTISTS LIST-------------------
@app.route('/artists')
def artists():
  data=[]
  artists = Artist.query.all()
  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name
    })
  
  return render_template('pages/artists.html', artists=data)

#-----------SEARCH FOR ARTISTS-------------
@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term=request.form.get('search_term','')
  search_result=Artist.query.filter(Artist.name.ilike(f'%{search_term}%'))
  response={
    "count": search_result.count(),
    "data": search_result
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

#-----------------DISPLAYING AN ARTIST'S PAGE-----------
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  #Using of JOIN queries to get past and upcoming shows
  #upcoming shows > current time, past shows < current time
  past_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.now()).all()
  past_shows = []
  upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows = []
  
  #displaying past and upcoming shows for the displayed artist
  for show in past_shows_query:
    past_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  for show in upcoming_shows_query:
    upcoming_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  
  #displaying data of the displayed artist
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_artist.html', artist=data)

#--------------------------EDITING & UPDATING ARTIST------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  artist_inf={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }
  return render_template('forms/edit_artist.html', form=form, artist=artist_inf)

#--------------------------------EDIT ARTIST SUBMISSION FORM---------------------
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    form = ArtistForm(request.form)
    artist = Artist.query.get(artist_id)

    artist.name = form.name.data
    artist.phone = form.phone.data
    artist.state = form.state.data
    artist.city = form.city.data
    artist.genres = form.genres.data
    artist.image_link = form.image_link.data
    artist.facebook_link = form.facebook_link.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data
    
    db.session.commit()
    flash('The Artist ' + request.form['name'] + ' has been successfully updated!')
  except:
    db.session.rollback()
    flash('An Error has occured, Update is not applied')
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))


#---------------CREATE AN ARTIST------------------------
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form)
  try:
    artist = Artist(
      name=form.name.data,
      city=form.city.data,
      state=form.state.data,
      phone=form.phone.data,
      image_link=form.image_link.data,
      facebook_link=form.facebook_link.data,
      seeking_venue=form.seeking_venue.data,
      seeking_description=form.seeking_description.data,
      genres=form.genres.data
    )
    db.session.add(artist)
    db.session.commit()
    #On succesive db insert, show message that artist was succesfully listed
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    #In case of failure, show message that an error occured
    flash('An error occurred. Artist '+ request.form['name'] + ' could not be listed')
  finally:
    db.session.close()
  return render_template('pages/home.html')


#***************************************************************************************************
#                                             SHOWS
#****************************************************************************************************

#--------------------------------------DISPLAYING SHOWS---------------------------------------
@app.route('/shows')
def shows():
  #Use JOIN queries to merge between shows, artists & venues related to each other
  shows_query = db.session.query(Show).join(Artist).join(Venue).all()  
  data=[]
  for show in shows_query: 
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name, 
      "artist_image_link": show.artist.image_link,
      'start_time': format_datetime(str(show.start_time))
    })
  return render_template('pages/shows.html', shows=data)

#-------------------------------CREATE A SHOW------------------------------------
@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form)
  try:
    show = Show(
       artist_id = form['artist_id'].data,
       venue_id = form['venue_id'].data,
       start_time= form['start_time'].data
    )
    db.session.add(show)
    db.session.commit()
  # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occured. show could not be listed')
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
