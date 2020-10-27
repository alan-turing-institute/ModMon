"""
Classes defining the ModMon database schema in the SQLAlchemy ORM
"""
# coding: utf-8
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Dataset(Base):
    """Unique combination of a start date, end date and database."""

    __tablename__ = "dataset"

    datasetid = Column(Integer, primary_key=True)

    databasename = Column(String(20))
    description = Column(String(500))
    start_date = Column(DateTime)
    end_date = Column(DateTime)


class Metric(Base):
    """Unique name and a description for each metric to be tracked. Names will come from
    the saved scores.csv files after model runs.
    """

    __tablename__ = "metric"

    metric = Column(String(50), primary_key=True)

    description = Column(String(500))


class ResearchQuestion(Base):
    """Question the model is trying to answer."""

    __tablename__ = "research_question"

    questionid = Column(Integer, primary_key=True)

    description = Column(String(500), nullable=False)


class Team(Base):
    """Details of the team submitting the model."""

    __tablename__ = "team"

    teamname = Column(String(50), primary_key=True)

    contactname = Column(String(100), nullable=False)
    contactemail = Column(String(100), nullable=False)
    description = Column(String(500))


class Model(Base):
    """Model table stores groups of unique question, team and model name combinations.
    Each model may have multiple Model Versionos (see ModelVersioni table)
    """

    __tablename__ = "model"

    modelid = Column(Integer, primary_key=True)

    teamname = Column(ForeignKey("team.teamname"), nullable=False)
    questionid = Column(ForeignKey("research_question.questionid"), nullable=False)

    name = Column(String(20), nullable=False)
    description = Column(String(500))

    researchquestion = relationship("ResearchQuestion")
    team = relationship("Team")


class ModelVersion(Base):
    """Version of a specified model. Each model version specifies the path to (location)
    its files and the commands needed to run it. The commands must contain placeholder
    arguments <start_date>, <end_date> and <database> which are replaced with
    appropriate values at run time.
    """

    __tablename__ = "model_version"

    modelid = Column(ForeignKey("model.modelid"), primary_key=True, nullable=False)
    modelversion = Column(String(10), primary_key=True, nullable=False)

    trainingdatasetid = Column(ForeignKey("dataset.datasetid"), nullable=False)
    testdatasetid = Column(ForeignKey("dataset.datasetid"), nullable=False)

    location = Column(String(500))
    score_command = Column(String(500))
    predict_command = Column(String(500))
    retrain_command = Column(String(500))
    modeltraintime = Column(DateTime)
    active = Column(Boolean)

    model = relationship("Model")
    dataset = relationship(
        "Dataset",
        primaryjoin="ModelVersion.testdatasetid == Dataset.datasetid",
    )
    dataset1 = relationship(
        "Dataset", primaryjoin="ModelVersion.trainingdatasetid == Dataset.datasetid"
    )


class Prediction(Base):
    """Each row in the Scores table is a value for a single metric from a run of a model
    version on a certain dataset.
    """

    __tablename__ = "prediction"
    __table_args__ = (
        ForeignKeyConstraint(
            ["modelid", "modelversion"],
            ["model_version.modelid", "model_version.modelversion"],
        ),
    )

    modelid = Column(Integer, primary_key=True, nullable=False)
    modelversion = Column(String(10), primary_key=True, nullable=False)
    datasetid = Column(
        ForeignKey("dataset.datasetid"), primary_key=True, nullable=False
    )
    runid = Column(Integer, primary_key=True, nullable=False)
    recordid = Column(Integer, primary_key=True, nullable=False)

    runtime = Column(DateTime, nullable=False)
    values = Column(JSON, nullable=False)

    modelversion1 = relationship("ModelVersion")
    dataset = relationship("Dataset")


class Score(Base):
    """Each row in the Scores table is a value for a single metric from a run of a model
    version on a certain dataset.
    """

    __tablename__ = "score"
    __table_args__ = (
        ForeignKeyConstraint(
            ["modelid", "modelversion"],
            ["model_version.modelid", "model_version.modelversion"],
        ),
    )

    modelid = Column(Integer, primary_key=True, nullable=False)
    modelversion = Column(String(10), primary_key=True, nullable=False)
    datasetid = Column(
        ForeignKey("dataset.datasetid"), primary_key=True, nullable=False
    )
    runid = Column(Integer, primary_key=True, nullable=False)
    metric = Column(ForeignKey("metric.metric"), primary_key=True, nullable=False)

    isreference = Column(Boolean, nullable=False)
    runtime = Column(DateTime, nullable=False)
    value = Column(Float(53), nullable=False)

    metric1 = relationship("Metric")
    modelversion1 = relationship("ModelVersion")
    dataset = relationship("Dataset")
