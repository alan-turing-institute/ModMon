# Toy Model 1 (Multiclass Example)

## Dataset and Features

[SEER 9 November 2019 submission](https://seer.cancer.gov/data-software/documentation/seerstat/nov2019/):
- Most years available, but smallest geographic coverage
- 9 registries: San Francisco-Oakland, Connecticut, Detroit, Hawaii, Iowa, New Mexico, Seattle, Utah, Atlanta
- Covers approximately 9.4% of the U.S. population (based on 2010 census)
- Contains one record for each of 5,347,692 tumours. From this we extract roughly 730,000 breast cancer tumours.
- Patients diagnosed between 1975 and 2017.

Features included:
- Age
- Year of diagnosis
- Cause of Death
- Tumour markers (prognostic indicators)
- Involvement of nodes
- Extent of disease
- Number of tumours
- Cancer stage

Some features are only available for certain periods of time, or their encoding changes.

## Model/Question

The features included and the question posed are heavily inspired by these papers:
- [Deep Multi-task Gaussian Processes for Survival Analysis with Competing Risks](https://proceedings.neurips.cc/paper/2017/file/861dc9bd7f4e7dd3cccd534d0ae2a2e9-Paper.pdf)
- [Multitask Boosting for Survival Analysis with Competing Risks](https://proceedings.neurips.cc/paper/2018/file/2afe4567e1bf64d32a5527244d104cea-Paper.pdf)
- [Tree-based Bayesian Mixture Model for Competing Risks](http://proceedings.mlr.press/v84/bellot18a/bellot18a.pdf)
- [DeepHit: A Deep Learning Approach to Survival Analysis with Competing Risks](http://medianetlab.ee.ucla.edu/papers/AAAI_2018_DeepHit#:~:text=DeepHit%20makes%20no%20assumptions%20about,one%20possible%20event%20of%20interest)

We train a Random Forest classifier to predict patient outcomes ten years after breast cancer diagnosis in four categories:
- Alive
- Died from breast cancer
- Died from diseases of the heart
- Died from other causes

## ModMon

What's described below is the status of the ModMon database as created by running `run_multiclass.sh`.

1. Train a first model using all patients diagnosed between 1975 and 1979 (inclusive).
2. Generate predictions with and test (evaluate the performance of) that model on patients diagnosed between 1980 and 1984.
3. Train a new model on all patients diagnosed between 1975 and 1984.
4. Generate predictions with and test (evaluate the performance of) all previous versions of the model on patients diagnosed between 1985 and 1989.
5. Repeat steps 3 and 4 in five year intervals until we reach patients diagnosed in 2007 (we have to stop 10 years before the end of the SEER data to be able to predict 10 year survival). So:
   - Train a model for 1975 to 1989
   - Test all previous models on 1990 to 1994
   - Train a model for 1975 to 1994
   - Test all previous models on 1995 to 1999
   - Train a model for 1975 to 1999
   - Test all previous models on 2000 to 2004
   - Train a model for 1975 to 2004
   - Test all previous models on 2005-2007

Note that:
- Patients diagnosed between 1975 and 1979 are used for training the first model only and we don't generate predictions for them in the database.
- In total there are 6 different model versions (1975-1979, 1975-1984, 1975-1989, 1975-1994, 1975-1999, and 1975-2004).