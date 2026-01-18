import json

def application(environ, start_response):
    method = environ.get('REQUEST_METHOD', 'GET')
    path = environ.get('PATH_INFO', '/')
    get_params = {}
    query_string = environ.get('QUERY_STRING', '')
    if query_string:
        for pair in query_string.split('&'):
            if '=' in pair:
                key, value = pair.split('=', 1)
                get_params[key] = value
    post_params = {}
    if method == 'POST':
        try:
            content_length = int(environ.get('CONTENT_LENGTH', 0))
        except ValueError:
            content_length = 0
        if content_length > 0:
            body = environ['wsgi.input'].read(content_length)
            content_type = environ.get('CONTENT_TYPE', '')
            if 'application/json' in content_type:
                post_params = json.loads(body.decode('utf-8'))
            else:
                body_str = body.decode('utf-8', errors='ignore')
                for pair in body_str.split('&'):
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        post_params[key] = value
    output_lines = []
    output_lines.append(f"WSGI Test App on port 8081")
    output_lines.append(f"Method: {method}")
    output_lines.append(f"Path: {path}")
    output_lines.append("")
    output_lines.append("GET Parameters:")
    for key, value in get_params.items():
        output_lines.append(f"  {key}: {value}")
    output_lines.append("")
    output_lines.append("POST Parameters:")
    if post_params:
        for key, value in post_params.items():
            output_lines.append(f"  {key}: {value}")
    output_lines.append("")
    response_text = '\n'.join(output_lines)
    status = '200 OK'
    response_headers = [
        ('Content-type', 'text/plain; charset=utf-8'),
        ('Content-Length', str(len(response_text.encode('utf-8'))))
    ]
    start_response(status, response_headers)
    return [response_text.encode('utf-8')]