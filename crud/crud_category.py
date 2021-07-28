from slugify import slugify
from sqlalchemy.orm import Session

from crud.base import CRUDBase
from models.catalogue import Category


class CRUDCategory(CRUDBase):
    def bulk(self, session: Session, objs_in):
        if objs_in is not None and len(objs_in) > 0:
            categories = []

            for category in objs_in:
                if session.query(Category).filter(Category.category == category.category).exists():
                    continue

                categories.append(
                    Category(
                        category=category.category,
                        slug=slugify(category.category)
                    )
                )

            session.add_all(categories)
            session.commit()

    def update(
            self,
            session,
            db_obj,
            data_dict
    ):
        if data_dict.get("category", None) is not None:
            data_dict["slug"] = slugify(data_dict["category"])

        return super(CRUDCategory, self).update(session, db_obj, data_dict)
