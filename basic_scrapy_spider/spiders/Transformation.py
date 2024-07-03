import json
import os
from pathlib import Path


def transform_json(data):
    if isinstance(data, dict):
        return [{k: transform_json(v) for k, v in data.items()}]
    elif isinstance(data, list):
        return [transform_json(item) for item in data]
    else:
        return data


def process_file(input_path, output_path):
    with open(input_path, 'r') as f:
        data = json.load(f)

    # Transform only request_parameters and response_elements
    transformed_data = {
        "action": data["action"],
        "request_parameters": transform_json(data["request_parameters"])[0],
        "response_elements": transform_json(data["response_elements"])[0]
    }

    with open(output_path, 'w') as f:
        json.dump(transformed_data, f, indent=2)


def main():
    input_dir = Path('aws_action_data')
    output_dir = Path('transformed')

    # Create the output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)

    for file in input_dir.glob('aws_action_*.json'):
        output_file = output_dir / file.name
        process_file(file, output_file)
        print(f"Processed {file.name}")


if __name__ == "__main__":
    main()