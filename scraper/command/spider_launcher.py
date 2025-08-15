import subprocess
import yaml

def launch_spiders(registry_path):
    with open(registry_path) as file:
        config = yaml.safe_load(file)
        for spider in config['spiders']:
            command = ['scrapy', 'crawl', spider['name'],
                '-a', f"config={spider['config']}"
            ]
            if 'args' in spider:
                command.extend(spider['args'])
            
            print(f"Launching spider: {spider['name']} with args: {spider.get('args', [])}")
            subprocess.run(command)

if __name__ == '__main__':
    launch_spiders('command/registry.yaml')        