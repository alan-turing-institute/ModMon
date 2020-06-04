DROP TABLE IF EXISTS results;
DROP TABLE IF EXISTS datasets;
DROP TABLE IF EXISTS modelVersions;
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
  description VARCHAR(500) NOT NULL, -- TODO: longer if needed (research question)
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
  name VARCHAR(20),
  description VARCHAR(500),
  PRIMARY KEY (modelID),
  FOREIGN KEY (teamName) REFERENCES teams (teamName),
  FOREIGN KEY (questionID) REFERENCES researchQuestions (questionID)
);

-- The second set of tables are populated by the model validator
-- each time they run a model and get some output data

CREATE TABLE modelVersions (
  modelID INT NOT NULL,
  modelVersion VARCHAR(10) NOT NULL,
  datasetID INT NOT NULL, -- dataset the model was trained on
  location VARCHAR(500), -- path to model file and prediction script TODO: is this something that is appropriate to be stored in the database (perhaps an evironment script too)
  command VARCHAR(500), -- to run the model prediction script
  modelTrainTime TIMESTAMP,
  active BOOLEAN, -- submission of a new model should turn this off, default on
  PRIMARY KEY (modelID, modelVersion),
  FOREIGN KEY (modelID) REFERENCES models (modelID)
);

CREATE TABLE datasets (
  datasetID INT NOT NULL,
  dataBaseName VARCHAR(20) NOT NULL,
  dataBaseVersionTime TIMESTAMP NOT NULL, -- either current TIMESTAMP or a TIMESTAMP in the past before an update was pushed to the db
  description VARCHAR(500), -- Must provide some info on how the analysts database query was modified, if it has been. Possibly entire query (save this for version 2?)
  start_date TIMESTAMP,
  end_date TIMESTAMP,
  PRIMARY KEY (datasetID)
);

-- DROP TABLE IF EXISTS modelMetrics; -- TODO: do we need this? I think covered by results table
-- CREATE TABLE modelMetrics (
--   modelID INT,
--   metric INT,
--   model INT,
--   active bool
-- );

CREATE TABLE results (
  -- id INT, TODO: Do we need a result id?
  modelID INT NOT NULL,
  modelVersion VARCHAR(10) NOT NULL,
  datasetID INT NOT NULL,
  runTime TIMESTAMP NOT NULL,
  metric VARCHAR(20) NOT NULL,
  value FLOAT NOT NULL, -- TODO will this be a float for every metric?
  valueError FLOAT,
  resultMessage VARCHAR(500),
  PRIMARY KEY (modelID, modelVersion, datasetID, runTime, metric),
  FOREIGN KEY (modelID, modelVersion) REFERENCES modelVersions (modelID, modelVersion),
  FOREIGN KEY (datasetID) REFERENCES datasets (datasetID),
  FOREIGN KEY (metric) REFERENCES metrics (metric)
);
