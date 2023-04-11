from jsonschema import validate, ValidationError

import json

from typing import Union
from pathlib import Path


# constants
CONFIG_JSON_SCHEMA = {
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'additionalProperties': False,
    'type': 'object',
    'properties': {
        'mqtt': {
            'additionalProperties': False,
            'type': 'object',
            'properties': {
                'enabled': {
                    'type': 'boolean',
                },
                'host': {
                    'type': 'string',
                },
                'port': {
                    'type': 'number',
                    'minimum': 1,
                    'maximum': 65535,
                },
                'client_id': {
                    'type': 'string',
                },
                'tls_config': {
                    'additionalProperties': False,
                    'type': 'object'
                },
                'login': {
                    'type': 'object',
                    'properties': {
                        'username': {
                            'type': 'string'
                        },
                        'password': {
                            'type': 'string'
                        }
                    },
                    'required': [
                        'username',
                        'password'
                    ]
                },
                'publish': {
                    'additionalProperties': False,
                    'type': 'object',
                    'properties': {
                        'topic_prefix': {
                            'type': 'string',
                        },
                        'json_path_topic_depth': {
                            'type': 'number',
                            'minimum': 0
                        },
                        'request_file_in_message_content': {
                            'type': 'boolean'
                        }
                    }
                }
            },
            'required': [
                'enabled'
            ]
        },
        'api': {
            'additionalProperties': False,
            'type': 'object',
            'properties': {
                'files': {
                    'type': 'object',
                    'minProperties': 1,
                    'patternProperties': {
                        '[a-z]+': {
                            'type': 'object',
                            'properties': {
                                'path': {
                                    'type': 'string'
                                },
                                'schema': {
                                    'type': 'string',
                                    'default': ''
                                },
                                'default': {
                                    'type': 'boolean',
                                    'default': False
                                }
                            },
                            'required': [
                                'path'
                            ]
                        }
                    }
                }
            },
            'required': [
                'files'
            ]
        }
    },
    'required': [
        'mqtt',
        'api'
    ]
}

MQTT_DEFAULT_CONFIG_VALUES = {
    'enabled': False,
    'host': '127.0.0.1',
    'port': 1883,
    'client_id': '<auto>',
    'publish': {
      'topic_prefix': '',
      'json_path_topic_depth': 0,
      'request_file_in_message_content': False
    }
}

API_FILES_DEFAULT_CONFIG_VALUES = {
    'schema': '',
    'default': False
}


class Singleton(type):

    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__call__(*args, **kwargs)

        return cls._instance


class Config(dict, metaclass=Singleton):

    def __init__(self, config_file_path: Union[str, Path]):
        super().__init__(**self._load(config_file_path))

    @staticmethod
    def _load(config_file_path: Union[str, Path]) -> dict:
        """
        Loads and validates the JSON configuration
        :param config_file_path: Path to the JSON configuration file
        :return: configuration data as dict
        """

        with open(config_file_path, 'r') as config_file_handler:
            configuration = json.load(config_file_handler)

            try:
                validate(configuration, CONFIG_JSON_SCHEMA)

            except ValidationError as validation_error:
                raise ValueError(validation_error)

        # add default options to missing configurations
        configuration['mqtt'] = MQTT_DEFAULT_CONFIG_VALUES | configuration['mqtt']
        configuration['mqtt']['publish'] = \
            MQTT_DEFAULT_CONFIG_VALUES['publish'] | configuration['mqtt']['publish']

        for file in configuration['api']['files']:
            configuration['api']['files'][file] = \
                {**API_FILES_DEFAULT_CONFIG_VALUES, **configuration['api']['files'][file]}

        # convert all sub dicts in config in SimpleNamespace objects
        # iter_list = list()
        # configuration_iter = iter(configuration)
        # while True:
        #     try:
        #         key = next(configuration_iter)
        #
        #         value = configuration[key]
        #         if isinstance(value, dict):
        #             iter_list.append((key, configuration, configuration_iter))
        #             configuration, configuration_iter = value, iter(value)
        #
        #     except StopIteration:
        #         if (iter_list_len := len(iter_list)) > 0:
        #             # line below has the same behavior as a LIFO
        #             key, configuration, configuration_iter = iter_list.pop(iter_list_len - 1)
        #             configuration[key] = SimpleNamespace(**configuration[key])
        #
        #         else:
        #             break

        return configuration
