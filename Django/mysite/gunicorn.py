import multiprocessing
bind = "0.0.0.0:8000"
workers = 3
worker_class = "sync"
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
proc_name = "rosoha_gunicorn"
daemon = False