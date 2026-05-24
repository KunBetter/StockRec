from datetime import date, datetime
from typing import Any, Generic, Optional, TypeVar

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from backend.persistence.database import Base

T = TypeVar("T", bound=Base)


class Repository(Generic[T]):
    def __init__(self, session: Session, model: type[T]):
        self.session = session
        self.model = model

    def get_by_id(self, id: int) -> Optional[T]:
        return self.session.get(self.model, id)

    def get_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        stmt = select(self.model).limit(limit).offset(offset)
        return list(self.session.scalars(stmt).all())

    def find_by(self, **kwargs) -> list[T]:
        stmt = select(self.model).filter_by(**kwargs)
        return list(self.session.scalars(stmt).all())

    def find_one_by(self, **kwargs) -> Optional[T]:
        stmt = select(self.model).filter_by(**kwargs)
        return self.session.scalars(stmt).first()

    def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.flush()
        return instance

    def update_by_id(self, id: int, **kwargs) -> bool:
        stmt = update(self.model).where(self.model.id == id).values(**kwargs)
        result = self.session.execute(stmt)
        return result.rowcount > 0

    def delete_by_id(self, id: int) -> bool:
        stmt = delete(self.model).where(self.model.id == id)
        result = self.session.execute(stmt)
        return result.rowcount > 0

    def upsert(self, unique_keys: dict, data: dict) -> T:
        existing = self.find_one_by(**unique_keys)
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            existing.updated_at = datetime.utcnow()
            self.session.flush()
            return existing
        merged = {**unique_keys, **data}
        return self.create(**merged)

    def count(self, **kwargs) -> int:
        stmt = select(func.count()).filter_by(**kwargs)
        return self.session.scalar(stmt) or 0

    def bulk_create(self, items: list[dict]) -> int:
        instances = [self.model(**item) for item in items]
        self.session.add_all(instances)
        self.session.flush()
        return len(instances)
