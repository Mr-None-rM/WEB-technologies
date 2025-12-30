import multiprocessing
from urllib.parse import parse_qs

def app(environ, start_response):
    print(multiprocessing.cpu_count())
    method = environ.get('REQUEST_METHOD', 'GET')
    get_data = parse_qs(environ.get('QUERY_STRING', ''))
    post_data = {}
    if method == 'POST':
        try:
            cl = environ.get('CONTENT_LENGTH', '0')
            if cl.isdigit() and int(cl) > 0:
                body = environ['wsgi.input'].read(int(cl))
                post_data = parse_qs(body.decode('utf-8'))
        except:
            pass
    out = []
    if get_data:
        out.append("GET:\n")
        for k, v in get_data.items():
            out.append(f"{k}={v[0]}\n")
    if post_data:
        if out:
            out.append("\n")
        out.append("POST:\n")
        for k, v in post_data.items():
            out.append(f"{k}={v[0]}\n")
    if not out:
        out.append("No parameters\n")
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [line.encode() for line in out]
application = app