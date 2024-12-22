from backups3 import app, exceptions, log
from dotenv import load_dotenv

if __name__ == "__main__":
    try:
        load_dotenv()
        log.configure_logger()
        app = app.App()
        app.run()
    except exceptions.InitException as e:
        print(f"Error starting application: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
