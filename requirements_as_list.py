""" returns installed pip packages as list"""

import pkg_resources
import json

installed_packages = pkg_resources.working_set
installed_packages_list = sorted(
    ["%s==%s" % (i.key, i.version) for i in installed_packages]
)
# print(installed_packages_list)

print(f"Saving requirements in requirements_list.json...")

json_file = open("requirements_list.json", "w")
json.dump(installed_packages_list, json_file, indent=2, ensure_ascii=False)
