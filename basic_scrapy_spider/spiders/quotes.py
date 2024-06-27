import scrapy
import json


class AWSScrapeSpider(scrapy.Spider):
    name = "AWS_Scrape"

    def start_requests(self):
        # List of actions to scrape
        data_list = ['CreateInternetGateway']
        for action in data_list:
            AWS_Action_URL = f'https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_{action}.html'
            yield scrapy.Request(url=AWS_Action_URL, callback=self.parse_action, meta={'action': action})

    def parse_action(self, response):
        action = response.meta['action']

        # Action Name
        action_name = response.css('h1.topictitle::text').get().strip()

        # Request Parameters
        request_parameters = {}
        request_params_section = response.xpath(
            f'//h2[@id="API_{action}_RequestParameters"]/following-sibling::div[@class="variablelist"]//dl')

        # Flag to stop parsing request parameters
        parsing_request_params = True

        for dl in request_params_section:
            dts = dl.xpath('dt')
            dds = dl.xpath('dd')

            for dt, dd in zip(dts, dds):
                key = dt.css('span.term b::text').get().strip()
                param_type = dd.xpath('p[contains(text(), "Type:")]/text()').get()
                required = dd.xpath('p[contains(text(), "Required:")]/text()').get()

                if param_type:
                    param_type = param_type.replace("Type:", "").strip()

                if parsing_request_params:
                    if param_type in ['Boolean', 'String']:
                        request_parameters[key] = ""
                    else:
                        request_parameters[key] = ""
                else:
                    break  # Stop parsing request parameters once we encounter Response Elements

                # Check if we should stop parsing request parameters
                if dt.xpath(f'span[@id="API_{action}_ResponseElements"]'):
                    parsing_request_params = False

        # Response Elements
        response_elements = {}
        response_elements_section = response.xpath(
            f'//h2[@id="API_{action}_ResponseElements"]/following-sibling::div[@class="variablelist"]//dl')
        for dl in response_elements_section:
            dts = dl.xpath('dt')
            dds = dl.xpath('dd')

            for dt, dd in zip(dts, dds):
                key = dt.css('span.term b::text').get().strip()
                elem_type = dd.xpath('p[contains(text(), "Type:")]/text()').get()

                if elem_type:
                    elem_type = elem_type.replace("Type:", "").strip()

                if elem_type in ['Boolean', 'String']:
                    response_elements[key] = ""
                else:
                    response_elements[key] = ""

                next_h2_id = dt.xpath('following-sibling::h2/@id').get()
                if next_h2_id == f"API_{action}_ResponseElements":
                    break  # Stop parsing request parameters

        def remove_keys(request_params, response_elements):
            for key in response_elements:
                if key in request_params:
                    del request_params[key]

        remove_keys(request_parameters, response_elements)
        # Create a dictionary to hold the action data
        action_data = {
            'action': action_name,
            'request_parameters': request_parameters,
            'response_elements': response_elements
        }

        # Save data to a JSON file
        with open(f'aws_action_{action}.json', 'w') as json_file:
            json.dump(action_data, json_file, indent=4)

        self.log(f"Data for {action} has been scraped and saved to aws_action_{action}.json")
