# Run as follows:
# Delete previous outputs:
#	make clean
# Calculate metrics between start and end idx:
#	make START_IDX=<start_idx> END_IDX=<end_idx>

all: metrics.json

predictions.csv:
	python predict.py --start_idx $(START_IDX) --end_idx $(END_IDX)

metrics.json: predictions.csv
	python metrics.py

clean:
	rm -f metrics.json
	rm -f predictions.csv