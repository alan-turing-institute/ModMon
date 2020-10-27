# Run as follows:
# Delete previous outputs:
#	make clean
# Calculate metrics between start and end idx:
#	make START_DATE=<start_date> END_DATE=<end_date> DATABASE=<database>

all: scores.csv

model.txt:
	python train.py --start_date $(START_DATE) --end_date $(END_DATE) --database $(DATABASE)

predictions.csv predictions.json:
	python predict.py --start_date $(START_DATE) --end_date $(END_DATE) --database $(DATABASE)

scores.csv: predictions.csv
	python metrics.py

clean:
	rm -f scores.csv
	rm -f predictions.csv
	rm -f predictions.json

cleanmodel:
	rm -f model.txt
