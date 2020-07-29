import logging
import matplotlib.pyplot as plt
import numpy as np
import os
import pyodbc
import psycopg2
import pandas as pd
import seaborn as sns
import unittest

# import plotting and tabling decorators, and sql query function for caching
from utils import plotting, table, check_statement, cached_sql_query

# import global config file
from configlib import config

pd.plotting.register_matplotlib_converters()
logger = logging.getLogger(__name__)

class TestModMon(unittest.TestCase):
    """This report aims to provide readers with a summary of the model appraisal"""

    db_connection = None

    @classmethod
    def setUpClass(cls):
        """Set up database connection before running tests."""
        cls.db_connection = psycopg2.connect(
            host=config["db_login"]["server"],
            port=config["db_login"]["port"],
            database=config["db_login"]["db_name"],
        )

        logger.info("Connected to the database.")
        logger.info("Saving outputs to %s", config["plots"]["save_dir"])
        os.makedirs(config["plots"]["save_dir"], exist_ok=True)
        with open(config["plots"]["save_dir"] + "/" + "intro.md", "w") as f:
            f.write(cls.__doc__)

    @classmethod
    def tearDownClass(cls):
        """Close connection to database after completing and/or failing tests."""
        cls.db_connection.close()
        logger.info("Closed connection to the database.")

    @plotting
    def test_fig_results_per_model_plot(self):
        """Numbers of each model in results table"""
        query = """
        SELECT m.name, COUNT( DISTINCT r.runid )
        FROM results AS r, models AS m
        WHERE r.modelid = m.modelid
        GROUP BY m.name;
        """
        model_runs = cached_sql_query(
            query,
            self.db_connection,
        )
        bar = sns.barplot(x='name', y='count', data=model_runs)
        bar.set(xlabel='Model', ylabel="Runs in ModMon DB")

    @plotting
    def test_fig_results_performance(self):
        """Scatter plots for each unique metric that measures model performance on a research question
        across database versions for all models that answer that question and each model version"""
        query = """
        SELECT m.name, r.metric, r.value, d.databasename, d.datasetid, m.modelid, r.modelversion, q.description
        FROM results AS r, datasets AS d, models AS m, researchQuestions AS q
        WHERE r.testdatasetid = d.datasetid
        AND r.modelid = m.modelid
        AND m.questionid = q.questionid
        AND NOT r.isreferenceresult;
        """
        results = cached_sql_query(
            query,
            self.db_connection,
        )
        results = results.sort_values(by=['modelid', 'datasetid'])

        results['model'] = results['name'] + '_' + results['modelversion']
        results['titles'] = results['metric'] + ' (' + results['description'] + ')'

        g = sns.FacetGrid(data=results, row='titles', sharey=False, sharex=False, aspect=3, hue='model')
        g.map(plt.scatter, "databasename", "value").fig.subplots_adjust(hspace=.4)
        g.set(xlabel='Database Version', ylabel='Metric Value')
        g.set_titles(col_template = "{col_name}", row_template = '{row_name}')
        for i, _ in enumerate(g.axes):
            g.axes[i][0].legend(title = "Models")
