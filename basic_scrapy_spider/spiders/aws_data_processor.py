import json
import os


def process_aws_data(data, processed_types=None):
    if processed_types is None:
        processed_types = set()

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                data[key] = process_aws_data(value, processed_types)
            elif isinstance(value, str) and value and value not in processed_types:
                processed_types.add(value)
                file_path = os.path.join('DataType_data', f'aws_DataType_{value}.json')
                if os.path.exists(file_path):
                    with open(file_path, 'r') as file:
                        type_data = json.load(file)
                    content_params = type_data.get('content_parameters', {})
                    if content_params:
                        data[key] = process_aws_data(content_params, processed_types)
                else:
                    print(f"File not found: {file_path}")
                    # Here you might want to trigger the spider to scrape this data type
                    # For now, we'll leave it as is
                    pass
    return data


def process_action_file(action):
    file_path = os.path.join('aws_action_data', f'aws_action_{action}.json')
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)

        data['request_parameters'] = process_aws_data(data.get('request_parameters', {}))
        data['response_elements'] = process_aws_data(data.get('response_elements', {}))

        # Save the processed data back to the file
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

        print(f"Processed data for {action}:")
        print(json.dumps(data, indent=4))
    else:
        print(f"File not found: {file_path}")