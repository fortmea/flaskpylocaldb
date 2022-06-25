pip install -r requirements.txt --force;
pip uninstall matplotlib;
if [ ! -f key.key ]; then
python generatekey.py
fi
python app.py