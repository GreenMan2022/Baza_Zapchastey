from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Component(Base):
    __tablename__ = 'components'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String)
    seller_link = Column(Text)
    price = Column(Float)
    parsing_method = Column(String)      # 'xpath', 'class', 'id', 'css'
    parsing_pattern = Column(String)     # строка c xpath/class/id/css


class DeviceComponent(Base):
    __tablename__ = 'device_components'
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'))
    component_id = Column(Integer, ForeignKey('components.id'))
    quantity = Column(Integer, default=1)
    component = relationship('Component')


class Device(Base):
    __tablename__ = 'devices'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    components = relationship('DeviceComponent', cascade='all, delete-orphan')
