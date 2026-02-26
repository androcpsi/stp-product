import logging
from waitress import serve
from stdpalletingproduct.wsgi import application

# Setup logging
logging.basicConfig(filename='django_waitress.log', level=logging.DEBUG,
                    format='%(asctime)s %(message)s')

if __name__ == "__main__":
    logging.info("Server started")
    try:
        serve(application, host='0.0.0.0', port=8080)
    except Exception as e:
        logging.error(f"Error starting server: {e}")