from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, BigInteger, Table, Text, Column, Integer, String, Text, MetaData, ForeignKey
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
engine = create_engine('sqlite:///:memory:')
Session = sessionmaker(bind=engine)


class Peer(Base):
    __tablename__ = 'peers'

    id = Column(Integer, primary_key=True)
    session_id = Column(BigInteger)

    subscriptions = relationship('Subscription', backref='peer')


class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True)
    topic = Column(Text)
    peer_id = Column(Integer, ForeignKey('peers.id'))


Base.metadata.create_all(engine)
