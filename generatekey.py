from pylocaldatabase import pylocaldatabase
dbcontroll = pylocaldatabase.databasecontroller(path="db.json", isEncrypted=False)
dbcontroll.generateKey("key.key")
