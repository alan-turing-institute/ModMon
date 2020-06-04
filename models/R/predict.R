# Change to this script's directory and run it as follows:
#     Rscript predict.R <START_IDX> <END_IDX>
# Where <START_IDX> and <END_IDX> are replaced with integers representing
# the first and last index in the data to predict and calculate the
# metrics for.

library(tidyverse)
library(glmnet)
library(caret)
library(RJSONIO)
library(argparse)

# Parse command line arguments
args <- commandArgs(trailingOnly=TRUE)

if (length(args)!= 2) {
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
metrics <- list(
  RMSE = RMSE(predictions, wine$quality),
  Rsquare = R2(predictions, wine$quality)
)
print(paste(c("RMSE:", metrics$RMSE, ", Rsquare:", metrics$Rsquare),
            collapse=" "))
# Save metrics to file
exportJson <- toJSON(metrics)
write(exportJson, "metrics.json")
