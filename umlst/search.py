import requests

from umlst.auth import Authenticator


class Search(Authenticator):
    def __init__(self, api_key: str):
        super(Search, self).__init__(api_key=api_key)
        version = 'current'
        content_endpoint = "/rest/search/" + version
        base_uri = "https://uts-ws.nlm.nih.gov"
        self.search_uri = base_uri + content_endpoint

    def find(self, string: str):

        page_number = 0

        while True:
            ##generate a new service ticket for each page if needed
            page_number += 1
            query = {'string': string, 'ticket': self.get_ticket(),
                     'pageNumber': page_number}
            # query['includeObsolete'] = 'true'
            # query['includeSuppressible'] = 'true'
            # query['returnIdType'] = "sourceConcept"
            # query['sabs'] = "SNOMEDCT_US"
            r = requests.get(self.search_uri, params=query, verify=False)
            items = r.json()
            jsonData = items["result"]
            # print (json.dumps(items, indent = 4))

            print("Results for page " + str(page_number) + "\n")

            for result in jsonData["results"]:
                print("ui: " + result["ui"])
                print("uri: " + result["uri"])
                print("name: " + result["name"])
                print("Source Vocabulary: " + result["rootSource"])

                print("\n")

            ##Either our search returned nothing, or we're at the end
            if jsonData["results"][0]["ui"] == "NONE":
                break
            print("*********")

        pass
