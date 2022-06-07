pip install -r requirements.txt --force;
if [ ! -f key.key ]; then
python generatekey.py
fi
python app.py