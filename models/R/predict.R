# Change to this script's directory and run it as follows:
#     Rscript predict.R <START_DATE> <END_DATE> <DATABASE>
# Where <START_DATE> and <END_DATE> are replaced with integers representing
# the first and last index in the data to predict and calculate the
# metrics for.

library(tidyverse)
library(glmnet)
library(caret)
library(argparse)

# Parse command line arguments
args <- commandArgs(trailingOnly=TRUE)

if (length(args) < 2) {
  stop("Two arguments must be supplied: start_idx and end_idx",
       call.=FALSE)
} else {
  start_idx <- as.integer(args[1])
  end_idx <- as.integer(args[2])
  print(paste(c("start_idx:", start_idx, ", end_idx:", end_idx),
              collapse=" "))
}

# load the model
model <- readRDS("./model.rds")

# read in data
wine <- read.csv(file = "winequality-white.csv", sep = ";")
wine <- as_tibble(wine)

# select rows to predict
wine <- wine %>% slice(start_idx:end_idx)

# Make predictions on the test data
x.test <- model.matrix(quality ~., wine)[,-1]
predictions <- model %>% predict(x.test) %>% as.vector()

# Model performance metrics
df <- data.frame(
  metric = c("RMSE", "Rsquare"),
  value = c(RMSE(predictions, wine$quality), R2(predictions, wine$quality))
)
print(df)

# Save metrics to file
write.csv(df, "metrics.csv", row.names=FALSE)
