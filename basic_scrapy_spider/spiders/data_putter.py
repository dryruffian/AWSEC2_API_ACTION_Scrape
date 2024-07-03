import json
import os

def file_to_list(filename):
    """Read a file and return its contents as a list of stripped lines."""
    try:
        with open(filename, 'r') as file:
            return [line.strip() for line in file]
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        return []

def load_json(filename):
    """Load JSON data from a file."""
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: The file '{filename}' contains invalid JSON.")
        return {}

def save_json(filename, data):
    """Save JSON data to a file."""
    try:
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
    except IOError:
        print(f"Error: Could not write to file '{filename}'.")

def process_actions(actions_file, template_file, output_dir):
    """Process actions from a file and save the transformed data to the output directory."""
    actions = file_to_list(actions_file)
    template = load_json(template_file)

    for action in actions:
        scrap_data = load_json(f'transformed/aws_action_{action}.json')
        if scrap_data:
            template['requestParameters'] = scrap_data['request_parameters']
            template['responseElements'] = scrap_data['response_elements']
            template['eventName'] = scrap_data['action']
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f'aws_final_{action}.json')
            save_json(output_file, template)

if __name__ == "__main__":
    process_actions('Action.txt', 'Temp.json', 'Final_Action_data')
