from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine, Index
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class Scan(Base):
    __tablename__ = "wifi_scans"
    id = Column(Integer, primary_key=True)
    ssid = Column(String(64), index=True)          # e.g., "UTS-Visitor"
    bssid_hash = Column(String(64), index=True)    # hashed MAC
    channel = Column(Integer, index=True)          # 1..165
    ts = Column(DateTime, index=True)              # UTC time
    rssi = Column(Float)                           # -90..-20 dBm
    lat = Column(Float, nullable=True)             # optional
    lon = Column(Float, nullable=True)             # optional

def get_session(db_url="sqlite:///wifi.db"):
    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)
    # Composite index helps multi-field filtering
    Index("idx_scans_multi", Scan.ssid, Scan.bssid_hash, Scan.channel, Scan.ts)
    Session = sessionmaker(bind=engine, future=True)
    return Session()
