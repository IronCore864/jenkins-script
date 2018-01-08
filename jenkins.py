import os
import logging
import configparser
import requests
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning

import jinja2

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

cfg = configparser.ConfigParser()
cfg.read(os.path.join(os.path.dirname(__file__), "cfg.ini"))

AUTH = HTTPBasicAuth(cfg['JENKINS']['user'], cfg['JENKINS']['password'])
HOST = cfg['JENKINS']['host']
PROTOCOL = cfg['JENKINS']['protocol']

module_logger = logging.getLogger('main.utils.jenkins')


def job_exists(job_name):
    get_job_url = '{protocol}://{jenkins_host}/checkJobName?value={job_name}'.format(
        protocol=PROTOCOL, jenkins_host=HOST, job_name=job_name)
    r = requests.get(get_job_url, auth=AUTH, verify=False)
    return True if "job already exists" in r.text else False


def create_job(job_name, context, template):
    """
    :param job_name: job_name to be created
    :param config: config xml for the job, type str
    :return: True if success, else False
    """
    create_job_url = '{protocol}://{host}/createItem?name={job_name}'.format(
        protocol=PROTOCOL, host=HOST, job_name=job_name)
    r = requests.post(create_job_url,
                      data=_generate_jenkins_job_config_xml(context, template),
                      headers=_build_headers(),
                      auth=AUTH,
                      verify=False)

    if r.status_code != 200:
        module_logger.error("Job creation failed!")
        module_logger.error(r.content)
        return False
    return True


def _generate_jenkins_job_config_xml(context, template):
    jenkins_job_xml_config = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "../templates/"))
    ).get_template(template).render(context)
    return jenkins_job_xml_config


def _get_crumb():
    get_crumb_url = '{protocol}://{jenkins_host}/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,":",//crumb)' \
        .format(protocol=PROTOCOL, jenkins_host=HOST)
    r = requests.get(get_crumb_url, auth=AUTH, verify=False)
    return r.text.split(':')[1]


def _build_headers():
    return {'Jenkins-Crumb': _get_crumb(), 'Content-Type': 'text/xml'}
