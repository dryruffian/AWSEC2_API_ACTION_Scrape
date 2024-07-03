import json
import os
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor, defer
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from Main import AWSScrapeSpider

configure_logging()
settings = get_project_settings()
runner = CrawlerRunner(settings)


@defer.inlineCallbacks
def run_spider(data_type):
    print(f"Starting to crawl {data_type}")
    yield runner.crawl(AWSScrapeSpider, data_list=data_type)
    print(f"Finished crawling {data_type}")


@defer.inlineCallbacks
def process_aws_data_async(data, processed_types=None):
    print("Entering process_aws_data_async")
    if processed_types is None:
        processed_types = set()

    if isinstance(data, dict):
        for key, value in list(data.items()):
            print(f"Processing key: {key}")
            if isinstance(value, list):
                print(f"Processing list for key: {key}")
                data[key] = yield process_aws_data_async(value, processed_types)
            elif isinstance(value, str) and value and value not in processed_types:
                processed_types.add(value)
                file_path = os.path.join('DataType_data', f'aws_DataType_{value}.json')
                print(f"Checking file: {file_path}")
                if not os.path.exists(file_path):
                    print(f"File not found: {file_path}. Running spider for {value}")
                    yield run_spider(value)
                    yield defer.succeed(None)

                if os.path.exists(file_path):
                    print(f"Processing file: {file_path}")
                    with open(file_path, 'r') as file:
                        type_data = json.load(file)
                    content_params = type_data.get('content_parameters', {})
                    if content_params:
                        print(f"Processing content parameters for {value}")
                        data[key] = yield process_aws_data_async(content_params, processed_types)
    print("Exiting process_aws_data_async")
    defer.returnValue(data)


@defer.inlineCallbacks
def process_action_file(action):
    print(f"Processing action file for {action}")
    file_path = os.path.join('aws_action_data', f'aws_action_{action}.json')
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)

        print("Processing request parameters")
        data['request_parameters'] = yield process_aws_data_async(data.get('request_parameters', {}))
        print("Processing response elements")
        data['response_elements'] = yield process_aws_data_async(data.get('response_elements', {}))

        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

        print(f"Processed data for {action}:")
        print(json.dumps(data, indent=4))
    else:
        print(f"File not found: {file_path}")


def file_to_list(filename):
    print(f"Reading file: {filename}")
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            return [line.strip() for line in lines]
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        return []


@defer.inlineCallbacks
def main():
    print("Starting main function")
    action_list = file_to_list('Action.txt')
    print(f"Actions to process: {action_list}")

    for i in range(0, 4):
        for action in action_list:
            print(f"Processing action: {action}")
            file_path = os.path.join('aws_action_data', f'aws_action_{action}.json')
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}. Running spider for {action}")
                yield run_spider(action)
                yield defer.succeed(None)
            else:
                yield process_action_file(action)
    print("Finished processing all actions")
    reactor.stop()


if __name__ == "__main__":
    print("Starting script")
    reactor.callWhenRunning(main)
    reactor.run()
    print("Script finished")
