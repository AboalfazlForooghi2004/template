import yaml
import os
import sys
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = 'switch_data.yaml'
TEMPLATE_FILE = 'cisco_template.j2'
OUTPUT_FILE = 'final_config.txt'

def main():
    try:
        data_path = os.path.join(BASE_DIR, DATA_FILE)
        
        with open(data_path, encoding='utf-8') as f:
            data = yaml.safe_load(f)

        env = Environment(
            loader=FileSystemLoader(BASE_DIR),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        template = env.get_template(TEMPLATE_FILE)
        output = template.render(data)

        print("---Output of the generated configuration---")
        print(output)

        output_path = os.path.join(BASE_DIR, OUTPUT_FILE)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
            
        print(f"--- Success! Config saved to: {OUTPUT_FILE} ---")

    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: YAML syntax issue - {e}")
        sys.exit(1)
    except TemplateNotFound:
        print(f"Error: Template file '{TEMPLATE_FILE}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()