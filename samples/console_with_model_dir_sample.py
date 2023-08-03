from pyfireconsole.db.connection import FirestoreConnection
from pyfireconsole import PyFireConsole


# Before running, put your model files e.g. "app/models/user.py"

# Run console
FirestoreConnection().initialize(project_id="YOUR_PROJECT_ID")
PyFireConsole(model_dir="app/models").run()
