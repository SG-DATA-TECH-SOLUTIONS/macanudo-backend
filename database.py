from google.cloud import firestore

# The `project` parameter is optional and represents which project the client
# will act on behalf of. If not supplied, the client falls back to the default
# project inferred from the environment.
db = firestore.Client(project="macanudo-479414", database="macanudo")

# Test connection by listing collections (read-only operation)
print("Connected to Firestore successfully!")
print(f"Project: {db.project}")
print(f"Database: macanudo")

# Uncomment below to write data (requires write permissions):
doc_ref = db.collection("users").document("alovelace")
doc_ref.set({"first": "Ada", "last": "Lovelace", "born": 1815})
print("Document written successfully!")
