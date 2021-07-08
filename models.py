from app import db

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(150), nullable=False)
    state = db.Column(db.String(150), nullable=True)
    address = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(150))
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(200))
    genres = db.Column("genres",db.ARRAY(db.String()), nullable=False)
    website_link = db.Column(db.String(200))
    seeking_talent = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String(300))
    shows = db.relationship('Show', backref='venue', lazy=True, cascade="all, delete")

    def __repr__(self):
      return f"<Venue {self.id} name: {self.name}>"



class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=True)
    seeking_description=db.Column(db.String(300))
    shows = db.relationship('Show', backref='artist', lazy=True, cascade="all, delete")
    
    def __repr__(self):
      return f"<Artis {self.id} name: {self.name}>"
    
class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id', ondelete='CASCADE'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id', ondelete='CASCADE'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
      return f"<Show {self.id}, Artist {self.artist_id}, Venue {self.venue_id}>"
