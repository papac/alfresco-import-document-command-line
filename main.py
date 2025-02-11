import argparse
import requests
import base64
import csv
# import ftfy

class AlfrescoObjectFetcher():

    def __init__(self, args):
        self.base_folder_url = "{}/alfresco/api/-default-/public/cmis/versions/1.1/browser/root/{}"
        self.headers = self.setHeader(args.username, args.password)
        output = open(args.output, 'w')
        self.output = csv.DictWriter(
            output, ['name', 'url', 'id', 'title', 'is_folder'], delimiter=";")
        self.output.writeheader()
        self.args = args
        self.dispatch(args)

    def setHeader(self, username, password):
        data = "{}:{}".format(username, password)
        encoded = str(base64.b64encode(data.encode("utf-8")), "utf-8")
        return {
            'Content-Type': "application/json",
            'Authorization': "Basic {}".format(encoded),
            'Accept': "*/*",
            'Cache-Control': "no-cache",
            'Accept-Encoding': "gzip, deflate",
            'Connection': "keep-alive",
        }

    def get_root_node_children(self, url):
        responses = requests.request("GET", url, headers=self.headers)
        if responses.status_code == 200:
            return responses.json()
        return None

    def node_hierachy(self, al_folders):
        nodes = []
        if al_folders is None:
            return nodes

        for item in al_folders["objects"]:
            node = None
            path = None
            object_id = None
            title = None
            for it in item["object"]["properties"]:
                if it == "cmis:name":
                    node = item["object"]["properties"][it]['value']
                if it == "cmis:path":
                    path = item["object"]["properties"][it]['value']
                if it == "cmis:objectId":
                    object_id = item["object"]["properties"][it]['value']
                if it == "cm:title":
                    title = item["object"]["properties"][it]['value']
            nodes.append({"name": node, "path": path,
                          "object_id": object_id,
                          "service": path.split("/")[-1],
                          "is_folder": True,
                          "title": title})
        return nodes

    def save_base_folder(self, node):
        self.output.writerow(node)

    def recursive_folder_loader(self, path, name, autoload, object_id, title, isFolder):
        # Build URL
        base_url = None
        if autoload:
            base_url = path
        else:
            base_url = self.build_url(path)

        response = self.get_root_node_children(base_url)
        if len(response['objects']) > 0:
            if isFolder:
                out = {"name":  self.convert_iso_name_to_string(name),  "url": base_url, "id": object_id,
                       "title": self.convert_iso_name_to_string(title), "is_folder": 1}
                self.save_base_folder(out)
            nodes = self.isFolders(response, base_url, name)
            if nodes:
                for node in nodes:
                    if node['is_folder']:
                        self.recursive_folder_loader(
                            self.convert_iso_name_to_string(node['path']),
                            self.convert_iso_name_to_string(node['path']),
                            True,
                            node['object_id'],
                            self.convert_iso_name_to_string(node['title']),
                            node['is_folder']
                        )
        else:
            output = {"name": name,  "url": base_url, "id": object_id,
                      "title": title, "is_folder": 1}
            self.output.writerow(output)

    def isFolders(self, folders, base_url, ph):
        nodes = []
        for item in folders["objects"]:
            isFolder = False
            name = None
            path = None
            object_id = None
            title = None
            for it in item["object"]["properties"]:
                if it == "cmis:objectTypeId":
                    if item["object"]["properties"][it]['value'] == "cmis:folder":
                        isFolder = True
                if it == "cmis:name":
                    name = self.convert_iso_name_to_string(item["object"]["properties"][it]['value'])
                if it == "cmis:path":
                    path = item["object"]["properties"][it]['value']
                if it == "cmis:objectId":
                    object_id = item["object"]["properties"][it]['value']
                if it == "cm:title":
                    title = self.convert_iso_name_to_string(item["object"]["properties"][it]['value'])
            #'name', 'url', 'id', 'filetype'
            output = {}
            if isFolder:
                nodes.append({
                    "title": title,
                    "path": base_url + "/" + name,
                    "is_folder": isFolder,
                    "name": name,
                    "object_id": object_id
                })

                path = base_url + "/" + name
                output = {"name": name,  "url": path, "id": object_id,
                          "title": title, "is_folder": 1}
            else:
                path = base_url + "/" + name
                output = {"name": name,  "url": path, "id": object_id,
                          "title": title, "is_folder": 0}

            self.output.writerow(output)

        return nodes

    def dispatch(self, args):
        path = ""
        if args.servicename is None:
            path = args.root_folder
        else:
            path = "{}/{}".format(args.root_folder, args.servicename)
        url = self.build_url(path)
        nodes = self.node_hierachy(self.get_root_node_children(url))
        for node in nodes:
            self.recursive_folder_loader(
                self.convert_iso_name_to_string(node["path"][1:]),
                self.convert_iso_name_to_string(node["name"]),
                False,
                node['object_id'],
                self.convert_iso_name_to_string(node['title']),
                node['is_folder']
            )

    def build_url(self, path):
        return self.base_folder_url.format(self.args.hostname, path)

    def convert_iso_name_to_string(self, str):
        return str
        # if name is None:
        #     return ""
        # result = []
        # for word in name.split():
        #     # result.append(ftfy.fix_text(word))
        #     result.append(word)
        # return ' '.join(result)

def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-sn', '--servicename', help='Service name')
    parser.add_argument('-hn', '--hostname',
                        help='Alfresco host url or hostname')
    parser.add_argument('-rf', '--root_folder', help='Alfresco base folder')
    parser.add_argument('-u', '--username', help='Alfresco auth username')
    parser.add_argument('-p', '--password', help='Alfresco auth password')
    parser.add_argument('-o', '--output', help='Output file', required=True)
    parser.add_argument(
        '--verbose', help='Show command output', action='store_true')
    args = parser.parse_args()

    return args

if __name__ == "__main__":
    AlfrescoObjectFetcher(arg_parser())
