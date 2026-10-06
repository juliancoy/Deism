#!/usr/bin/env python3
"""Add Deism's static site and an isolated OrgPortal fixture stack to Docker."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
# Never serve a checked-in or leftover build without regenerating current source.
subprocess.run([sys.executable, str(root / 'scripts/build-local.py')], check=True)
portal = root.parent / 'OrgPortal'
state = root / '.local'
state.mkdir(exist_ok=True)
network = os.environ.get('DEISM_DOCKER_NETWORK', 'bmoremedtech')
portal_port = int(os.environ.get('DEISM_PORTAL_PORT', '8444'))
site_port = int(os.environ.get('DEISM_SITE_PORT', '8878'))
prefix = 'deism-'
# Writable local fixtures and credentials must never use a production read replica.
os.environ.update({
    'ORGPORTAL_LOCAL_STATE_DIR': str(state / 'orgportal'),
    'ORGPORTAL_LOCAL_GATEWAY_PORT': str(portal_port),
    'ORGPORTAL_LOCAL_TENANT_HOST': 'portal.deism.church',
    'ORGPORTAL_ORGANIZATION_REPLICA_SOURCE': '',
    'ORGPORTAL_START_PROD': 'false',
    'PIDP_EMAIL_VERIFICATION_DELIVERY': 'log',
})
sys.path.insert(0, str(portal))
spec = importlib.util.spec_from_file_location('deism_orgportal_launcher', portal / 'run.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
if os.environ.get('DEISM_SITE_ONLY') == '1':
    pass
elif os.environ.get('DEISM_REUSE_RUNNING') == '1':
    for service, port in [('org', 8001), ('chat', 8003), ('pidp-dev', 8000)]:
        launcher._wait_for_http(f'http://{prefix}{service}:{port}/health', network, retries=120, expect_status=200)
    launcher._start_local_gateway(prefix, network, prefix + 'portal-dev', prefix + 'org', prefix + 'pidp-dev', '8001')
else:
    launcher.run(prefix, network)
fixture = state / 'tenant.sql'
fixture.write_text(f"""
UPDATE portal_tenants SET hostname='portal.deism.church',
 public_base_url='https://localhost:{portal_port}', canonical_path_prefix='',
 custom_domain_status='attached', home_url='http://localhost:{site_port}/',
 feature_config=json_set(feature_config,
 '$.specialtyResources[0].href','http://localhost:{site_port}/',
 '$.specialtyResources[1].label','Hadith Curriculum',
 '$.specialtyResources[1].href','http://localhost:{site_port}/hadith/curriculum.html')
WHERE id='deism';
INSERT INTO events (id, ingest_key, title, slug, description, starts_at, ends_at,
 location, host_org_id, host_org_name, tags)
SELECT 'deism-local-gathering', 'local:deism:gathering',
 'Deism Local Community Gathering', 'deism-local-community-gathering',
 'An isolated local event for browser validation.',
 strftime('%Y-%m-%dT18:00:00Z','now','+7 days'),
 strftime('%Y-%m-%dT19:00:00Z','now','+7 days'),
 'Local test venue', organization_id, 'Church of God (Deist)', '["deism","local-test"]'
FROM portal_tenants WHERE id='deism'
ON CONFLICT(id) DO NOTHING;
""")
subprocess.run(['docker', 'cp', str(fixture), 'deism-org:/tmp/deism-tenant.sql'], check=True)
subprocess.run(['docker', 'exec', 'deism-org', 'node_modules/.bin/wrangler', 'd1', 'execute', 'org', '--local', '--file', '/tmp/deism-tenant.sql'], check=True)
config = state / 'site.conf'
config.write_text(f"""events {{}}
http {{
 include /etc/nginx/mime.types;
 default_type application/octet-stream;
 server {{
  listen 8080;
  root /site;
  location = /community {{ return 302 https://localhost:{portal_port}/; }}
  location = /login {{ return 302 https://localhost:{portal_port}/users/login; }}
  location / {{
   sub_filter_once on;
   sub_filter '</nav>' '<a href="https://localhost:{portal_port}/">Community Portal</a><a href="https://localhost:{portal_port}/users/login">Login</a></nav>';
   sub_filter '</ul>' '<li><a href="https://localhost:{portal_port}/">Community Portal</a></li><li><a href="https://localhost:{portal_port}/users/login">Login</a></li></ul>';
   try_files $uri $uri.html $uri/ =404;
  }}
 }}
}}
""")
launcher._remove_container('deism-site')
launcher.docker_utils.run_container({
    'image': 'nginx:alpine', 'name': 'deism-site', 'network': network,
    'detach': True, 'restart_policy': {'Name': 'always'},
    'ports': {'8080/tcp': ('127.0.0.1', site_port)},
    'volumes': {str(root / 'build'): {'bind': '/site', 'mode': 'ro'},
                str(config): {'bind': '/etc/nginx/nginx.conf', 'mode': 'ro'}},
})
print(f'Deism website: http://localhost:{site_port}/')
print(f'Deism portal: https://localhost:{portal_port}/')
