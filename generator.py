
from __future__ import annotations
import argparse
import logging
import os
import sys
from typing import Any, Dict, List
import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Jinja2 template with YAML data to generate device config.")
    parser.add_argument("--data", "-d", default=os.path.join(BASE_DIR, "switch_data.yaml"), help="Path to YAML data file.")
    parser.add_argument("--template", "-t", default=os.path.join(BASE_DIR, "cisco_template.j2"), help="Path to Jinja2 template file.")
    parser.add_argument("--output", "-o", default=os.path.join(BASE_DIR, "final_config.txt"), help="Path to output file.")
    parser.add_argument("--strict", action="store_true", help="Fail on minor validation warnings (be strict about required fields).")
    return parser.parse_args()


def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        raise ValueError(f"YAML file '{path}' is empty.")
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping/object (got {type(data).__name__}).")
    return data


def validate_data(data: Dict[str, Any]) -> List[str]:
    """
    Perform basic validation on the loaded YAML data.
    Returns a list of validation error messages (empty if valid).
    """
    errors: List[str] = []

    # Required top-level keys (adjust as needed for your template)
    required_keys = ["hostname", "device_type"]
    for k in required_keys:
        if k not in data:
            errors.append(f"Missing required top-level key: '{k}'")

    # interfaces should be a list if present
    if "interfaces" in data:
        if not isinstance(data["interfaces"], list):
            errors.append("Key 'interfaces' must be a list")
        else:
            for i, iface in enumerate(data["interfaces"], start=1):
                if not isinstance(iface, dict):
                    errors.append(f"Interface #{i} must be a mapping/object")
                    continue
                if "name" not in iface:
                    errors.append(f"Interface #{i} missing 'name'")
                if "mode" in iface and iface["mode"] not in ("access", "trunk"):
                    errors.append(f"Interface '{iface.get('name','?')}' has invalid mode '{iface.get('mode')}' (expected 'access' or 'trunk')")

    # vlans if present must be list of mappings with id
    if "vlans" in data:
        if not isinstance(data["vlans"], list):
            errors.append("Key 'vlans' must be a list")
        else:
            for v in data["vlans"]:
                if not isinstance(v, dict) or "id" not in v:
                    errors.append("Each VLAN must be a mapping with at least an 'id' key")

    # ntp_servers if present should be list
    if "ntp_servers" in data and not isinstance(data["ntp_servers"], list):
        errors.append("Key 'ntp_servers' must be a list")

    return errors


def render_template(template_path: str, data: Dict[str, Any]) -> str:
    env = Environment(
        loader=FileSystemLoader(os.path.dirname(template_path) or "."),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template_name = os.path.basename(template_path)
    template = env.get_template(template_name)
    # render using keyword args so top-level keys are accessible directly in template
    return template.render(**data)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()

    try:
        logging.info("Loading YAML data from: %s", args.data)
        data = load_yaml(args.data)

        logging.info("Validating data...")
        validation_errors = validate_data(data)
        if validation_errors:
            for e in validation_errors:
                logging.error("Validation: %s", e)
            if args.strict:
                logging.error("Validation failed (strict mode). Aborting.")
                return 1
            else:
                logging.warning("Validation produced warnings. Proceeding because strict mode is off.")

        logging.info("Rendering template: %s", args.template)
        output = render_template(args.template, data)

        logging.info("Writing output to: %s", args.output)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)

        logging.info("Success: config written to %s", args.output)
        return 0

    except FileNotFoundError as e:
        logging.error("File not found: %s", e)
        return 1
    except yaml.YAMLError as e:
        logging.error("YAML parsing error: %s", e)
        return 1
    except TemplateNotFound as e:
        logging.error("Template not found: %s", e)
        return 1
    except ValueError as e:
        logging.error("Validation error: %s", e)
        return 1
    except Exception as e:
        logging.exception("Unexpected error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())