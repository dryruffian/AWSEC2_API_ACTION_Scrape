import scrapy
import json
import os
from scrapy.crawler import CrawlerProcess


class AWSScrapeSpider(scrapy.Spider):
    name = "AWS_Scrape"
    scraped_data = []

    def start_requests(self):
        # List of actions to scrape
        for action, section_id in self.data_list:
            AWS_Action_URL = f'https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_{action}.html'
            yield scrapy.Request(url=AWS_Action_URL, callback=self.parse_action,
                                 meta={'action': action, 'section_id': section_id})

    def parse_action(self, response):
        action = response.meta['action']
        section_id = response.meta['section_id']

        # Action Name
        action_name = response.css('h1.topictitle::text').get().strip()

        # Parameters based on section_id
        parameters = self.extract_parameters(response, section_id)

        action_data = {
            'action': action_name,
            'parameters': parameters
        }

        self.scraped_data.append(action_data)

    def extract_parameters(self, response, section_id):
        parameters = {}
        params_section = response.xpath(
            f'//h2[@id="{section_id}"]/following-sibling::div[@class="variablelist"]//dl')

        for dl in params_section:
            dts = dl.xpath('dt')
            dds = dl.xpath('dd')

            for dt, dd in zip(dts, dds):
                key = dt.css('span.term b::text').get().strip()

                # Check if there is an <a> tag within the Type paragraph
                param_type_element = dd.xpath('p[contains(text(), "Type:")]/a')
                if param_type_element:
                    param_type_url = param_type_element.xpath('@href').get()
                    param_type_text = param_type_element.xpath('text()').get().strip()
                    parameters[key] = {'type': param_type_text, 'url': response.urljoin(param_type_url)}

                    # Follow the link to extract data from the linked page
                    yield scrapy.Request(url=response.urljoin(param_type_url), callback=self.parse_linked_page,
                                         meta={'key': key, 'parameters': parameters,
                                               'param_type_text': param_type_text})
                else:
                    parameters[key] = ""

        return parameters

    def parse_linked_page(self, response):
        key = response.meta['key']
        parameters = response.meta['parameters']
        param_type_text = response.meta['param_type_text']

        # Extract data from the linked page under the specified <h2> id
        linked_page_data = self.extract_linked_page_data(response, f'API_{param_type_text}_Contents')

        # Incorporate the linked page data into the parameters
        parameters[key]['linked_page_data'] = linked_page_data

    def extract_linked_page_data(self, response, section_id):
        # Extract the necessary data from the linked page under the specified <h2> id
        linked_page_data = {}
        content_section = response.xpath(f'//h2[@id="{section_id}"]/following-sibling::div[@class="variablelist"]//dl')

        for dl in content_section:
            dts = dl.xpath('dt')
            dds = dl.xpath('dd')

            for dt, dd in zip(dts, dds):
                key = dt.css('span.term b::text').get().strip()
                value = dd.xpath('string(.)').get().strip()
                linked_page_data[key] = value

        return linked_page_data

    def closed(self, reason):
        # Save all scraped data to a single JSON file
        output_dir = 'aws_action_data'
        os.makedirs(output_dir, exist_ok=True)

        with open(f'{output_dir}/aws_actions.json', 'w') as json_file:
            json.dump(self.scraped_data, json_file, indent=4)

        self.log(f"All scraped data saved to {output_dir}/aws_actions.json")


def scrape_aws_documentation(data_list):
    # Instantiate the spider class with data_list as an attribute
    AWSScrapeSpider.data_list = data_list

    # Run the spider using CrawlerProcess
    process = CrawlerProcess()
    process.crawl(AWSScrapeSpider)
    process.start()


def read_file_to_list(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            # Remove newline characters from each line
            lines = [line.strip() for line in lines if line.strip()]

            return lines
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []

# Read action and section id pairs from a file
data_list = read_file_to_list('Action.txt')
print(data_list)
scrape_aws_documentation(data_list)
