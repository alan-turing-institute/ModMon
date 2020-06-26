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
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Dataset(Base):
    __tablename__ = "datasets"

    datasetid = Column(Integer, primary_key=True)
    databasename = Column(String(20), nullable=False)
    description = Column(String(500))
    start_date = Column(DateTime)
    end_date = Column(DateTime)


class Metric(Base):
    __tablename__ = "metrics"

    metric = Column(String(20), primary_key=True)
    description = Column(String(500))


class Researchquestion(Base):
    __tablename__ = "researchquestions"

    questionid = Column(Integer, primary_key=True)
    description = Column(String(500), nullable=False)


class Team(Base):
    __tablename__ = "teams"

    teamname = Column(String(50), primary_key=True)
    contactname = Column(String(100), nullable=False)
    contactemail = Column(String(100), nullable=False)
    description = Column(String(500))


class Model(Base):
    __tablename__ = "models"

    modelid = Column(Integer, primary_key=True)
    teamname = Column(ForeignKey("teams.teamname"), nullable=False)
    questionid = Column(ForeignKey("researchquestions.questionid"), nullable=False)
    name = Column(String(20), nullable=False)
    description = Column(String(500))

    researchquestion = relationship("Researchquestion")
    team = relationship("Team")


class Modelversion(Base):
    __tablename__ = "modelversions"

    modelid = Column(ForeignKey("models.modelid"), primary_key=True, nullable=False)
    modelversion = Column(String(10), primary_key=True, nullable=False)
    trainingdatasetid = Column(ForeignKey("datasets.datasetid"), nullable=False)
    referencetestdatasetid = Column(ForeignKey("datasets.datasetid"), nullable=False)
    location = Column(String(500))
    command = Column(String(500))
    modeltraintime = Column(DateTime)
    active = Column(Boolean)

    model = relationship("Model")
    dataset = relationship(
        "Dataset",
        primaryjoin="Modelversion.referencetestdatasetid == Dataset.datasetid",
    )
    dataset1 = relationship(
        "Dataset", primaryjoin="Modelversion.trainingdatasetid == Dataset.datasetid"
    )


class Result(Base):
    __tablename__ = "results"
    __table_args__ = (
        ForeignKeyConstraint(
            ["modelid", "modelversion"],
            ["modelversions.modelid", "modelversions.modelversion"],
        ),
    )

    modelid = Column(Integer, primary_key=True, nullable=False)
    modelversion = Column(String(10), primary_key=True, nullable=False)
    testdatasetid = Column(
        ForeignKey("datasets.datasetid"), primary_key=True, nullable=False
    )
    isreferenceresult = Column(Boolean, nullable=False)
    runtime = Column(DateTime, nullable=False)
    runid = Column(Integer, primary_key=True, nullable=False)
    metric = Column(ForeignKey("metrics.metric"), primary_key=True, nullable=False)
    value = Column(Float(53), nullable=False)
    valueerror = Column(Float(53))
    resultmessage = Column(String(500))

    metric1 = relationship("Metric")
    modelversion1 = relationship("Modelversion")
    dataset = relationship("Dataset")
