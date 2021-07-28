import os
import shutil
from datetime import time
from typing import Any, Optional, List

from slugify import slugify
from sqlalchemy import case, cast, Integer
from sqlalchemy.orm import Session, aliased, joinedload
from sqlalchemy.sql import func
from sqlalchemy.sql.elements import Cast

from crud.base import CRUDBase
from elococo import main
from datetime import datetime
from models.catalogue import Product, ProductToProduct

elements = aliased(ProductToProduct)
boxes = aliased(ProductToProduct)
element = aliased(Product)


def reduction(box):
    return case(
        [
            (box.reduction_end > now().today(), box.reduction),
        ],
        else_=0
    )


def price_exact(box, reduction_=None):
    int_price = box.price

    if reduction_ is not None:
        return Cast(
            case(
                [
                    (reduction_ > 0, reduction_ * int_price / 100),
                ],
                else_=int_price
            ), Integer
        )

    return int_price


def price_exact_ht(box, price_alias):
    return Cast(case(
        [
            (box.is_ttc_price, price_alias * 100 / main.settings.TVA),
        ],
        else_=price_alias
    ), Integer)


def price_exact_ttc(box, price_alias):
    return Cast(
        case(
            [
                (box.is_ttc_price, price_alias),
            ], else_=price_alias * main.settings.TVA / 100
        ), Integer
    )


def product_query(session: Session, box):
    return session.query(
        box
    ).options(
        joinedload(box.categories),
        joinedload(box.images),
    ).join(
        box.elements.of_type(elements), isouter=True
    ).join(
        elements.element.of_type(element), isouter=True
    ).options(
        joinedload(box.boxes.of_type(boxes)).joinedload(boxes.box),
        joinedload(box.elements.of_type(elements)).joinedload(elements.element)
    )


def set_elements(session: Session, product_db, elements: List[schemas.catalogue.Elements]):
    for element_db in product_db.elements:
        session.delete(element_db)
    session.commit()

    if elements is not None and len(elements) > 0:
        associations = []

        for element in elements:
            if session.query(Product).filter(Product.id == element.product_id).first() is None:
                continue

            associations.append(
                ProductToProduct(
                    product_box_id=product_db.id,
                    product_element_id=element.product_id,
                    quantity=element.quantity
                )
            )

        session.add_all(associations)
        session.commit()
        return True

    return False


def set_categories(session, product_db, categories_id):
    if categories_id is not None and len(categories_id) > 0:
        categories_db = session.query(CategoryCreate).filter(
            CategoryCreate.id.in_(categories_id)
        ).all()
    else:
        categories_db = []

    product_db.categories = categories_db

    session.commit()


class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    def set_images(self, session, product_db, images):
        for image in product_db.images:
            path = main.settings.BASE_DIR / "medias" / image.path
            if os.path.exists(path):
                os.remove(path)
            session.delete(image)
        session.commit()

        models_product_images = []
        for image in images:
            filename = f"{time.time_ns()}.{image.filename.split('.')[-1]}"
            try:
                with open(main.settings.BASE_DIR / "medias" / filename, "wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)
            finally:
                image.file.close()

            models_product_images.append(
                ProductImage(path=filename, product_id=product_db.id)
            )

        product_db.images = models_product_images
        session.commit()

    def get(self, db: Session, id_: Any) -> Optional[Product]:
        box = aliased(Product)

        effective_stock_alias = case(
            [
                (
                    func.count(elements.product_element_id) > 0, func.min(
                        cast(
                            element.stock / elements.quantity, Integer
                        )
                    )
                ),
            ], else_=box.stock
        ).label("effective_stock")
        reduction_alias = reduction(box).label("effective_reduction")
        price_exact_label = price_exact(box, reduction_alias).label("price_exact")
        price_ht_alias = price_exact_ht(box, price_exact_label).label("price_ht")
        price_ttc_alias = price_exact_ttc(box, price_exact_label).label("price_ttc")

        q = product_query(
            db, box
        ).add_columns(
            effective_stock_alias, reduction_alias, price_ht_alias, price_ttc_alias
        ).filter(
            box.id == id_
        )

        q = q.first()

        product = q[0]
        product.effective_stock = q[1]
        product.effective_reduction = q[2]
        product.price_ht = q[3]
        product.price_ttc = q[4]

        return product

    def create(
            self, session: Session,
            obj_in: ProductCreate,
            elements: Optional[List[schemas.catalogue.Elements]] = None,
            categories_id: Optional[List[int]] = None
    ) -> Product:
        obj_in.date = obj_in.dateUpdate = now().date()
        product_db = Product(slug=slugify(obj_in.name), **obj_in.dict())
        session.add(product_db)
        session.commit()
        session.refresh(product_db)
        product_db = self.get(session, product_db.id)

        if elements is not None:
            set_categories(session, product_db, categories_id)

        if categories_id is not None:
            set_elements(session, product_db, elements)

        return product_db

    def update(
            self, db: Session,
            db_obj: Product,
            obj_in: ProductUpdate,
            elements: Optional[List[schemas.catalogue.Elements]] = None,
            categories_id: Optional[List[int]] = None
    ) -> Product:
        obj_in.dateUpdate = now().date()
        update_data = obj_in.dict(exclude_unset=True)

        if obj_in.name is not None:
            product.slug = slugify(obj_in.name)

        product_db = super().update(db, db_obj=db_obj, obj_in=update_data)

        if elements is not None:
            set_elements(db, product_db, elements)

        if categories_id is not None:
            set_categories(db, product_db, categories_id)

        return product_db


product = CRUDProduct(Product)
