clean-db:
	rm -f *.db

activate:
	. ./venv/bin/activate && pip install -r requirements.txt

run:
	python3 luxmed_sniper.py -c account.yaml luxmed_sniper.yaml

