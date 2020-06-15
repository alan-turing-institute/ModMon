DROP TABLE IF EXISTS results;
DROP TABLE IF EXISTS modelVersions;
DROP TABLE IF EXISTS datasets;
DROP TABLE IF EXISTS models;
DROP TABLE IF EXISTS metrics;
DROP TABLE IF EXISTS researchQuestions;
DROP TABLE IF EXISTS teams;

-- The first set of tables are populated with data that comes
-- directly from an analyst team

CREATE TABLE teams (
  teamName VARCHAR(50) NOT NULL,
  contactName VARCHAR(100) NOT NULL,
  contactEmail VARCHAR(100) NOT NULL,
  description VARCHAR(500),
  PRIMARY KEY (teamName)
);

CREATE TABLE researchQuestions (
  questionID INT NOT NULL,
  description VARCHAR(500) NOT NULL,
  PRIMARY KEY (questionID)
);

CREATE TABLE metrics (
  metric VARCHAR(20) NOT NULL,
  description VARCHAR(500),
  PRIMARY KEY (metric)
);

CREATE TABLE models (
  modelID INT NOT NULL,
  teamName VARCHAR(50) NOT NULL,
  questionID INT NOT NULL,
  name VARCHAR(20) NOT NULL,
  description VARCHAR(500),
  PRIMARY KEY (modelID),
  FOREIGN KEY (teamName) REFERENCES teams (teamName),
  FOREIGN KEY (questionID) REFERENCES researchQuestions (questionID)
);

CREATE TABLE datasets (
  datasetID INT NOT NULL,
  dataBaseName VARCHAR(20) NOT NULL,
  description VARCHAR(500), -- Must provide some info on how the analysts database query was modified, if it has been. Possibly entire query (save this for version 2?)
  start_date TIMESTAMP,
  end_date TIMESTAMP,
  PRIMARY KEY (datasetID)
);

-- The second set of tables are populated by the model validator
-- each time they run a model and get some output data

CREATE TABLE modelVersions (
  modelID INT NOT NULL,
  modelVersion VARCHAR(10) NOT NULL,
  trainingDatasetID INT NOT NULL,
  referenceTestDatasetID INT NOT NULL,
  -- location VARCHAR(500),
  command VARCHAR(500), -- to run the model prediction script
  modelTrainTime TIMESTAMP,
  active BOOLEAN, -- submission of a new model should turn this off, default on
  PRIMARY KEY (modelID, modelVersion),
  FOREIGN KEY (modelID) REFERENCES models (modelID),
  FOREIGN KEY (trainingDatasetID) REFERENCES datasets (datasetID),
  FOREIGN KEY (referenceTestDatasetID) REFERENCES datasets (datasetID)
);

CREATE TABLE results (
  modelID INT NOT NULL,
  modelVersion VARCHAR(10) NOT NULL,
  testDatasetID INT NOT NULL,
  isReferenceResult BOOLEAN NOT NULL,
  runTime TIMESTAMP NOT NULL,
  runID INT NOT NULL, -- rows that share this ID are from the same run of a model on a particular dataset
  metric VARCHAR(20) NOT NULL,
  value FLOAT NOT NULL,
  valueError FLOAT,
  resultMessage VARCHAR(500),
  PRIMARY KEY (modelID, modelVersion, testDatasetID, runID, metric),
  FOREIGN KEY (modelID, modelVersion) REFERENCES modelVersions (modelID, modelVersion),
  FOREIGN KEY (testDatasetID) REFERENCES datasets (datasetID),
  FOREIGN KEY (metric) REFERENCES metrics (metric)
);
