import yaml
import json

with open('docker-compose.yml', 'r') as file:
    docker_compose = yaml.safe_load(file)

containers = {}

for service, config in docker_compose['services'].items():
    containers[service] = {
        'image': config['image'],
        'environment': config.get('environment', {}),
    }

    if 'ports' in config:
        containers[service]['ports'] = {config['ports'][0].split(':')[0]: 'HTTP'}

with open('aws-lightsail-container.json', 'w') as outfile:
    json.dump(containers, outfile)