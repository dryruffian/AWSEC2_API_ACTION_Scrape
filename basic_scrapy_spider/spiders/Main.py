import scrapy
import json
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor, defer
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging
import os


class AWSScrapeSpider(scrapy.Spider):
    name = "AWS_Scrape"

    def __init__(self, data_list, *args, **kwargs):
        super(AWSScrapeSpider, self).__init__(*args, **kwargs)
        self.data_list = data_list
        self.results = {}

    def start_requests(self):
        action = self.data_list
        AWS_Action_URL = f'https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_{action}.html'
        yield scrapy.Request(url=AWS_Action_URL, callback=self.parse_action, meta={'action': action})

    def parse_action(self, response):
        action = response.meta['action']
        action_name = response.css('h1.topictitle::text').get().strip()
        request_parameters = self.extract_parameters(response, f'API_{action}_RequestParameters')
        response_elements = self.extract_parameters(response, f'API_{action}_ResponseElements')

        if not response_elements and not request_parameters:
            content_parameters = self.extract_parameters(response, f'API_{action}_Contents')
            action_data = {
                'action': action_name,
                'content_parameters': content_parameters,
            }
            output_dir = 'DataType_data'
            os.makedirs(output_dir, exist_ok=True)

            with open(f'{output_dir}/aws_DataType_{action}.json', 'w') as json_file:
                json.dump(action_data, json_file, indent=4)
        else:
            self.remove_keys(request_parameters, response_elements)
            action_data = {
                'action': action_name,
                'request_parameters': request_parameters,
                'response_elements': response_elements
            }
            output_dir = 'aws_action_data'
            os.makedirs(output_dir, exist_ok=True)

            with open(f'{output_dir}/aws_action_{action}.json', 'w') as json_file:
                json.dump(action_data, json_file, indent=4)

        self.log(f"Data for {action} has been scraped and saved to {output_dir}/aws_action_{action}.json")
        self.results[action] = action_data

    def extract_parameters(self, response, section_id):
        parameters = {}
        params_section = response.xpath(
            f'//h2[@id="{section_id}"]/following-sibling::div[@class="variablelist"]//dl')

        for dl in params_section:
            dts = dl.xpath('dt')
            dds = dl.xpath('dd')

            for dt, dd in zip(dts, dds):
                key = dt.css('span.term b::text').get().strip()
                param_type_element = dd.xpath('p[contains(text(), "Type:")]/a')
                if param_type_element:
                    param_type_text = param_type_element.xpath('text()').get().strip()
                    parameters[key] = param_type_text
                else:
                    parameters[key] = ""

        return parameters

    def remove_keys(self, request_parameters, response_elements):
        overlapping_keys = set(request_parameters.keys()) & set(response_elements.keys())
        for key in overlapping_keys:
            del request_parameters[key]


@defer.inlineCallbacks
def scrape_aws_documentation(data_list):
    configure_logging()
    settings = get_project_settings()
    runner = CrawlerRunner(settings)
    crawler = yield runner.crawl(AWSScrapeSpider, data_list=data_list)
    yield crawler.spider.results  # Wait for the spider to finish and return its results
    defer.returnValue(crawler.spider.results)


# @defer.inlineCallbacks
# def run_spider(data_list):
#     result = yield scrape_aws_documentation(data_list)
#     reactor.stop()
#     defer.returnValue(result)


if __name__ == "__main__":
    data = 'Tag'


    def print_results(result):
        print(f"Spider results: {result}")
        if result:
            print("Scraped data:")
            print(json.dumps(result, indent=2))
        else:
            print("No data was scraped. Check for errors in the spider execution.")


    scrape_aws_documentation(data)
