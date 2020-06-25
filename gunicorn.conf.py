import multiprocessing

bind = "unix:/run/gunicorn/socket"
# workers = multiprocessing.cpu_count() * 2 + 1
workers = 1
pid = "/run/gunicorn/pid"
accesslog = 'access.log'
errorlog = 'error.log'
