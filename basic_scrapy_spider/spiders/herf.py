import scrapy
import json
import os
from scrapy.crawler import CrawlerProcess


class AWSScrapeSpider(scrapy.Spider):
    name = "AWS_Scrape"

    def __init__(self, data_list, *args, **kwargs):
        super(AWSScrapeSpider, self).__init__(*args, **kwargs)
        self.data_list = data_list

    def start_requests(self):
        # List of actions to scrape
        for action in self.data_list:
            AWS_Action_URL = f'https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_{action}.html'
            yield scrapy.Request(url=AWS_Action_URL, callback=self.parse_action, meta={'action': action})

    def parse_action(self, response):
        action = response.meta['action']

        # Action Name
        action_name = response.css('h1.topictitle::text').get().strip()

        # Request Parameters
        request_parameters = self.extract_parameters(response, f'API_{action}_RequestParameters')

        # Response Elements
        response_elements = self.extract_parameters(response, f'API_{action}_ResponseElements')

        # Remove overlapping keys
        self.remove_keys(request_parameters, response_elements)

        action_data = {
            'action': action_name,
            'request_parameters': request_parameters,
            'response_elements': response_elements
        }

        output_dir = 'aws_action_data'
        os.makedirs(output_dir, exist_ok=True)

        # Save data to a JSON file
        with open(f'{output_dir}/aws_action_{action}.json', 'w') as json_file:
            json.dump(action_data, json_file, indent=4)

        self.log(f"Data for {action} has been scraped and saved to {output_dir}/aws_action_{action}.json")

    def extract_parameters(self, response, section_id):
        parameters = {}
        params_section = response.xpath(
            f'//h2[@id="{section_id}"]/following-sibling::div[@class="variablelist"]//dl')

        for dl in params_section:
            dts = dl.xpath('dt')
            dds = dl.xpath('dd')

            for dt, dd in zip(dts, dds):
                key = dt.css('span.term b::text').get().strip()

                # Extract the type of the parameter
                param_type_element = dd.xpath('p[contains(text(), "Type:")]/text()').re_first(r'Type:\s*(.*)')
                param_required_element = dd.xpath('p[contains(text(), "Required:")]/text()').re_first(r'Required:\s*(.*)')

                parameters[key] = {
                    'type': param_type_element.strip() if param_type_element else '',
                    'required': param_required_element.strip() if param_required_element else ''
                }

        return parameters

    def remove_keys(self, request_parameters, response_elements):
        overlapping_keys = set(request_parameters.keys()) & set(response_elements.keys())
        for key in overlapping_keys:
            del request_parameters[key]


def scrape_aws_documentation(data_list):
    process = CrawlerProcess()
    process.crawl(AWSScrapeSpider, data_list=data_list)
    process.start()


def read_file_to_list(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            lines = [line.strip() for line in lines if line.strip()]
            return lines
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []


if __name__ == "__main__":
    data_list = read_file_to_list('Action.txt')
    scrape_aws_documentation(data_list)
