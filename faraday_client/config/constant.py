"""
Faraday Penetration Test IDE
Copyright (C) 2014  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

"""
import os

CONST_REQUIREMENTS_FILE = 'requirements.txt'
CONST_FARADAY_HOME_PATH = os.path.join(os.getenv('FARADAY_HOME', os.path.expanduser('~/')), '.faraday')
CONST_FARADAY_IMAGES = 'images/'
CONST_FARADAY_LOGS_PATH = 'logs/'
CONST_FARADAY_FOLDER_LIST = [ "config", "data", "images",
                        "persistence",
                        "report", "temp", "zsh", "logs" ]

CONST_FARADAY_ZSHRC = "zsh/.zshrc"
CONST_FARADAY_ZSH_FARADAY = "zsh/faraday.zsh"
CONST_FARADAY_ZSH_OUTPUT_PATH = "zsh/output"
CONST_FARADAY_BASE_CFG = "config/default.xml"
CONST_FARADAY_USER_CFG = "config/config.xml"
CONST_LICENSES_DB = "faraday_licenses"
CONST_VULN_MODEL_DB = "cwe"

CONST_USER_HOME = "~"
CONST_USER_ZSHRC = "~/.zshrc"
CONST_ZSH_PATH = "zsh"
