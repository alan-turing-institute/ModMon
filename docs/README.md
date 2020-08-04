# ModMon Docs

- Overview (this page)
- [Installation and configuration](installation.md)
- [Required project/code structure](project_structure.md)
- [Adding a model to ModMon](model_submission.md)
- [Running models with ModMon](run_models.md)

## Context

Models represent the data they were trained on

If aspects of the data change the performance of a deployed model may drop

DECOVID happening in an uncertain, rapidly developing environment:
- pandemic changing (number of cases being treated, new treatments/improving practices, different lockdown measures in place etc.)
- project developing (data from new hospitals, new types of data/measurements added etc.)

DECOVID is therefore a prime example where the models or analyses developed at one time may not necessarily continue to perform as expected (or at least not as well as possible), and the timescale over which those changes happen and performance drops may be quite short.

As DECOVID outputs may be used to make clinical decisions for patients, it's critical to ensure that they stay relevant, or in other words to validate that any model being used still reflects the current status of the data.


## DECOVID Model Appraisal Proposal

We aim to provide a system where analysts can submit their models (or other analyses) to be easily run on new data as it arrives, and compare the results to previous runs. This is the ModMon package.

DECOVID teams will be answering many different research questions, with different programming languages (mostly python and R), packages (though limitied to what's available in the secure research environment) and workflows.

Being able to run models of completely different formats in one system requires some standardisation of the code that's provided. We have developed ModMon to be as workflow-agnostic as possible, with the main requirement being to provide a single command to run your model with up to three inputs defininig a dataset (a start date, end date and database name). The output of this command must be a CSV file containing the values of the metrics used to evaluate the performance of your model.

