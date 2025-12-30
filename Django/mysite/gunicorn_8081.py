import os
bind = "0.0.0.0:8081"
workers = 2
worker_class = "sync"
accesslog = "-"
errorlog = "-"
loglevel = "info"
reload = True
proc_name = "simple_wsgi_app"
daemon = False