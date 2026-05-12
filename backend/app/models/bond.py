from sqlalchemy import Column, Integer, Float, String, Date, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BondYield(Base):
    __tablename__ = "bond_yields"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    bond_type = Column(String, index=True) # "国债", "国开债", "农发债", "口行债", "地方政府债"
    
    y0 = Column(Float)
    m1 = Column(Float)
    m2 = Column(Float)
    m3 = Column(Float)
    m6 = Column(Float)
    m9 = Column(Float)
    y1 = Column(Float)
    y2 = Column(Float)
    y3 = Column(Float)
    y4 = Column(Float)
    y5 = Column(Float)
    y6 = Column(Float)
    y7 = Column(Float)
    y8 = Column(Float)
    y9 = Column(Float)
    y10 = Column(Float)
    y15 = Column(Float)
    y20 = Column(Float)
    y30 = Column(Float)
    y40 = Column(Float)
    y50 = Column(Float)

    __table_args__ = (UniqueConstraint('date', 'bond_type', name='_date_bond_type_uc'),)

class BondSpread(Base):
    __tablename__ = "bond_spreads"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True)
    s10y_2y = Column(Float)
    s5y_3y = Column(Float)
    s7y_5y = Column(Float)
    s10y_7y = Column(Float)

class BondQuantile(Base):
    __tablename__ = "bond_quantiles"

    id = Column(Integer, primary_key=True, index=True)
    indicator_name = Column(String, index=True) # e.g. "国开债-10Y"
    p10 = Column(Float)
    p25 = Column(Float)
    p50 = Column(Float)
    p75 = Column(Float)
    p90 = Column(Float)
    current_value = Column(Float)
    current_percentile = Column(Float)

class BenchmarkConfig(Base):
    __tablename__ = "benchmark_configs"
    id = Column(Integer, primary_key=True, index=True)
    tenor = Column(String, index=True) # "1Y", "2Y", ...
    bond_type = Column(String, index=True) # "国债", ...
    code = Column(String) # e.g. "230025.IB"
    
    __table_args__ = (UniqueConstraint('tenor', 'bond_type', name='_tenor_type_uc'),)

class BondHistory(Base):
    __tablename__ = "bond_histories"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, index=True)
    date = Column(Date, index=True)
    yield_val = Column(Float)
    
    __table_args__ = (UniqueConstraint('code', 'date', name='_code_date_uc'),)
