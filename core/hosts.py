from django_hosts import patterns, host

host_patterns = patterns(
    '',
    host(r'www', 'core.urls', name='www'),
    host(r'fillright', 'fillright.urls', name='fillright'),  # API subdomain
)