from sqlalchemy import func


def get_unique_id(session, column):
    """Get value one higher than the highest value in a SQL table column,
    where the column should be the SQL alchemy table column, e.g. Dataset.datasetid"""
    max_id = session.query(func.max(column)).scalar()
    if max_id:
        return max_id + 1
    return 1
