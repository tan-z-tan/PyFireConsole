import argparse

from pyfireconsole import FirestoreConnection, PyFireConsole


def main():
    parser = argparse.ArgumentParser(description="Run PyFireConsole with specified model directory and firestore setting.")
    parser.add_argument('--model-dir', required=False, help="Path to the model directory.")
    parser.add_argument('--project-id', required=False, help="Project ID for FirestoreConnection.")
    parser.add_argument('--service_account_key_path', required=False, help="Key path for FirestoreConnection.")

    args = parser.parse_args()

    FirestoreConnection().initialize(project_id=args.project_id, service_account_key_path=args.service_account_key_path)
    PyFireConsole(model_dir=args.model_dir).run()


if __name__ == '__main__':
    main()
