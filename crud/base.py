from sqlalchemy.orm import Session


class CRUDBase:
    def __init__(self, model):
        self.model = model

    def get(self, db: Session, id_):
        return db.query(self.model).filter(self.model.id == id_).first()

    def get_multi(
            self, session, skip=0, limit=100
    ):
        return session.query(self.model).offset(skip).limit(limit).all()

    def create(self, session, data_dict):
        db_obj = self.model(**data_dict)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def update(
            self,
            session,
            db_obj,
            data_dict
    ):
        for field in data_dict:
            setattr(db_obj, field, data_dict[field])

        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def remove(self, session, id_):
        obj = session.query(self.model).get(id_)
        session.delete(obj)
        session.commit()
        return obj
