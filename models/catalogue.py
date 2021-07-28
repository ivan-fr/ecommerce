from sqlalchemy import (
    Boolean, Column, Date, Integer, String, BigInteger, SmallInteger,
    Table, ForeignKey
)
from sqlalchemy.orm import relationship, backref

from orm.database import Base

association_product_category_table = Table(
    'association_product_category', Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id_', ondelete="CASCADE"), nullable=False),
    Column('category_id', Integer, ForeignKey('categories.id_', ondelete="CASCADE"), nullable=False)
)


class ProductToProduct(Base):
    __tablename__ = "association_product_product"

    product_box_id = Column(
        Integer, ForeignKey('products.id_', ondelete="CASCADE"), primary_key=True, nullable=False
    )
    product_element_id = Column(
        Integer, ForeignKey('products.id_', ondelete="CASCADE"), primary_key=True, nullable=False
    )
    quantity = Column(Integer, nullable=False)
    box = relationship("ProductOut", backref="elements", foreign_keys=[product_box_id])
    element = relationship("ProductOut", backref="boxes", foreign_keys=[product_element_id])


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False, unique=True)
    slug = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey('categories.id_', ondelete="CASCADE"), nullable=True)
    children = relationship(
        "CategoryCreate",
        backref=backref('parent', remote_side=[id]),
        lazy="joined",
        join_depth=2
    )


class ProductImage(Base):
    __tablename__ = "product_images"
    id = Column(Integer, primary_key=True)
    path = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey('products.id_', ondelete="CASCADE"), nullable=False)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    slug = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(BigInteger, nullable=False)
    is_ttc_price = Column(Boolean, default=False, nullable=False)

    reduction = Column(SmallInteger, nullable=True)
    reduction_end = Column(Date, nullable=True)

    stock = Column(Integer, nullable=False, default=0)

    date = Column(Date, nullable=False)
    dateUpdate = Column(Date, nullable=False)

    enable_sale = Column(Boolean, default=False)

    images = relationship(
        "ProductImage",
        backref="product",
    )

    categories = relationship(
        "CategoryCreate",
        secondary=association_product_category_table,
        backref="products"
    )
