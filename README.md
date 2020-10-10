# NetKAN-API
[🍕Buy me a Pizza](https://www.buymeacoffee.com/janbrohl>)

This is a proof of concept for a web-based API to make pull-requests to NetKAN ( https://github.com/KSP-CKAN/NetKAN ) so changes would only have to be approved by the KSP-CKAN team.

I tested it on a different repo and it seems to work so far but it is totally __NOT__ production-ready

Propably I will not put much (if any) work in this myself but I will happily merge pull requests.

## How can I try it?

### You need
- A fork of https://github.com/KSP-CKAN/NetKAN
- git
- Python 3.4+ (propably any 3.* will do but installation gets more complex)

### Run the server
- Create a new folder and put this repository's contents in it.
- Have a look at example-config.json and create your own config.json to suit your needs
- Create a [Virtual Environment](https://docs.python.org/3/library/venv.html) inside that folder and activate it.
- `python -m ensurepip --upgrade`
- `pip install -r requirements.txt`
- `python netkan_api.py`

### Upload a file

POST JSON data to http://127.0.0.1:8080/netkan/ModName-ModVersion
data must be of the form `{"entry":ContentsOfYourNetkanFile, "messsage":"Message To Add To The Pull Request"}`
