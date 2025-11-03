import os, sys
print("Python:", sys.version)
p = os.path.abspath("./firebase-admin-key.json")
print("Key path:", p, "exists?", os.path.exists(p))

from firebase_admin import credentials, initialize_app, firestore
cred = credentials.Certificate(p)
initialize_app(cred)
db = firestore.client()
print("Firestore client OK?", db is not None)

# Try a tiny write
doc = db.collection("users").document("local-test-user").collection("diagnostics").document("ping")
doc.set({"msg": "hello"})
print("Write OK")
