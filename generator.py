import yaml
from jinja2 import Environment, FileSystemLoader

with open('switch_data.yaml') as f:
    data = yaml.safe_load(f)

env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('cisco_template.j2')

output = template.render(data)

print("---Output of the generated configuration---")
print(output)

with open('final_config.txt', 'w') as f:
    f.write(output)
print("--- The file final_config.txt was successfully created.---")