"""SQLAlchemy ORM models.

Importing this package registers every model class on ``Base.metadata``.
Alembic's ``env.py`` and the test fixtures both rely on this side effect.
"""
from app.models.disease import Disease
from app.models.prediction import Prediction

__all__ = ["Disease", "Prediction"]
