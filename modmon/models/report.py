from os import devnull
import subprocess

from ..config import config


report_script = '''
import matplotlib.pyplot as plt
import psycopg2
import pandas as pd
import seaborn as sns
import unittest
from unitreport import plotting


class TestModMon(unittest.TestCase):
    """This report aims to provide readers with a summary of the model appraisal"""

    db_connection = None

    @classmethod
    def setUpClass(cls):
        """Set up database connection before running tests."""
        cls.db_connection = psycopg2.connect(
            host = "localhost",
            port = 5432,
            database = "ModMon",
        )

    @classmethod
    def tearDownClass(cls):
        """Close connection to database after completing and/or failing tests."""
        cls.db_connection.close()

    @plotting
    def test_fig_results_per_model_plot(self):
        """Numbers of each model in results table"""
        query = """
        SELECT m.name, COUNT( DISTINCT r.runid )
        FROM results AS r, models AS m
        WHERE r.modelid = m.modelid
        GROUP BY m.name;
        """
        model_runs = pd.read_sql(
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
        results = pd.read_sql(
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
'''


def generate_report():
    """Generate a html report containing plots found in test_modmon.py"""

    dev_null = open(devnull, "w")

    report_dir = config["reports"]["reportdir"]
    with open(report_dir + "/test_modmon.py", "w+") as unittest_file:
        unittest_file.write(report_script)

    subprocess.run(
        ["python", "-m", "unitreport", "--output_file", "model_appraisal.html"],
        check=True,
        cwd=report_dir,
        stdout=dev_null,
        stderr=dev_null,
    )
