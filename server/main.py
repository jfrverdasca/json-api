# external libs
import time

import uvicorn

from starlette.applications import Starlette
from starlette.endpoints import HTTPEndpoint
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.routing import Route
from paho.mqtt.client import Client
from jsonschema import validate, ValidationError

# python libs
import os
import sys
import json
import logging

from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from typing import Any, Union, List
from pathlib import Path
from uuid import uuid4

# project files
from config import Config

# constants
LOGGING_LEVEL = int(os.getenv('LOGGING_LEVEL', logging.INFO))
CONFIG = Config(Path(os.getenv('CONFIG_FILE', 'config.json')))
DEFAULT_JSON_FILE = next(iter(CONFIG['api']['files']))

# logging initialization
Path('logs').mkdir(exist_ok=True)  # create logs dir if not exist

logging.basicConfig(handlers=[RotatingFileHandler('logs/json-api.log', maxBytes=5242880, backupCount=2),
                              StreamHandler(sys.stderr)],
                    format='%(asctime)s - %(levelname)s:%(funcName)s:%(message)s')

logger = logging.getLogger('uvicorn')
logger.setLevel(level=LOGGING_LEVEL)

# others
mqtt_client: Client = Client(CONFIG['mqtt']['client_id'] if CONFIG['mqtt']['client_id'] != '<auto>' else uuid4().hex)


@mqtt_client.disconnect_callback()
def on_disconnect(client, userdata, rc):
    client.reconnect()


class JsonHandler(HTTPEndpoint):

    async def get(self, request: Request):
        return await self.process_request(request)

    async def put(self, request: Request):
        return await self.process_request(request)

    async def post(self, request: Request):
        return await self.process_request(request)

    async def delete(self, request: Request):
        return await self.process_request(request)

    async def process_request(self, request: Request):
        json_path = request.path_params['json_path']

        # path and request validation
        # validate path
        if json_path.endswith('/'):
            json_path = json_path[:-1]

        json_path_parts = json_path.split('/')
        for i, part in enumerate(json_path_parts):
            if (not part or ' ' in part) and i > 0:  # path "http://...:xxxx/ is valid and return all json content
                return Response(status_code=400)

            elif not part and i == 0:
                json_path_parts = []

        # check if url path specifies the json file to use
        request_file_data = CONFIG['api']['files'].get(DEFAULT_JSON_FILE)
        if len(json_path_parts) > 0 and json_path_parts[0] in CONFIG['api']['files']:
            request_file_data = CONFIG['api']['files'].get(json_path_parts.pop(0))

        # validate request and request body
        body = None
        method = request.method
        if method in ['POST', 'PUT']:
            try:
                body = await request.json()

            except json.JSONDecodeError as request_json_decode_error:
                logger.error(f'Malformed JSON in {method} request:', exc_info=request_json_decode_error)
                return Response('Invalid JSON request body', status_code=400)

        # change json data
        logger.debug(f'Performing \"{method}\" in JSON path {json_path_parts} with content {body}...')

        json_file_path = request_file_data['path']
        try:
            logger.debug(f'Loading the content of JSON file {json_file_path}')
            json_data = self.load_json_data(json_file_path)

            # if json file just contains a value, and we want to update just change the file content for the new value
            if method in ['POST', 'PUT'] and not json_path_parts:
                json_data = body

            else:
                # if json file just contains a value, but we have to create new nodes of given path
                if not isinstance(json_data, dict) and method in ['POST', 'PUT']:
                    json_data = dict()

                result = self.get_set_json_value_by_path(json_data, json_path_parts, method, body)
                if result is not None:  # no result value means operation is POST, PUT or DELETE
                    return JSONResponse(result)

            # json data has changed, so we need to save new version of data
            # NOTE: since objects in python are passed by reference, changes made inside functions to
            #       "json_data" variable are visible from outside the scope of the functions that changed them, so:
            logger.debug(f'Saving changes made to JSON content to file {json_file_path}')
            self.save_json_data(json_data,
                                json_file_path,
                                request_file_data['schema'] if request_file_data['schema'] else None)

        except FileNotFoundError:
            logger.error(f'File \"{json_file_path}\" not found')
            return Response(f'File \"{json_file_path}\" not found', status_code=400)

        except KeyError as key_error:
            logger.error(f'JSON node \"{key_error}\" not found. Path \"{json_path}\"')
            return Response(f'Not found \"{key_error}\"', status_code=404)

        except IndexError as index_error:
            logger.error(f'List index \"{index_error}\" is out of range')
            return Response(f'List index \"{index_error}\" is out of range', status_code=404)

        except json.JSONDecodeError as json_decode_error:
            logger.error(f'Malformed JSON file \"{json_file_path}\". '
                         f'Please correct the file the structure to be able to handle it:', exc_info=json_decode_error)
            return Response(f'Malformed JSON file \"{json_file_path}\". '
                            f'Please correct the file structure to be able to handle it. Detail: {json_decode_error}',
                            status_code=500)

        except ValidationError as json_validation_error:
            logger.info(f'The request violates the validations defined by the JSON schema:',
                        exc_info=json_validation_error)
            return Response(f'Request violates the validations defined by JSON schema: {json_validation_error}',
                            status_code=401)

        except ValueError:
            logger.error(f'Attempt to perform a \"{method}\" operation in JSON root node')
            return Response(f'Operation \"{method}\" cannot be performed in JSON root node', status_code=400)

        # publish json data changes to the broker if mqtt server is enabled
        if CONFIG['mqtt']['enabled']:
            logger.info(f'Publishing changes made to JSON...')
            try:
                self.publish_config(json_data if method != 'DELETE' else None,
                                    json_path_parts,
                                    json_file_path,
                                    path_depth=CONFIG['mqtt']['publish']['json_path_topic_depth'])

            except RuntimeError as mqtt_runtime_error:
                logger.error('Error occurred while publishing changes to broker:', exc_info=mqtt_runtime_error)
                return Response(status_code=500)

            except ValueError as mqtt_value_error:
                logger.error('Error occurred while publishing changes to broker:', exc_info=mqtt_value_error)
                return Response(status_code=500)

        return Response(status_code=200)

    @staticmethod
    def get_set_json_value_by_path(json_data: object, path: List[str],
                                   operation: str = 'get', value: Any = None):
        """
        Opens the JSON file and returns the node value to the given JSON path
        :param json_data: JSON data object
        :param path: path parts, in the JSON, to the node (ex: ['node1', 'node2', 'node3'])
        :param operation: Operation to perform in JSON like HTTP methods
        "GET" to get node value
        "POST" or "PUT" to create or update node value,
        "DELETE" to delete node
        :param value: new value to assign to node
        (Only assigned if operation is "POST" or "PUT", otherwise will be ignored)
        :return: Value of JSON node in the end of the path or nothing if operation is POST, PUT or DELETE.
                 Raise ValueError if path is empty and operation is POST, PUT or DELETE
                 Raise KeyError if path does not exist (only in GET or DELETE operations).
                 Raise IndexError list item index does not exist
        """

        operation = operation.lower()

        # if no path is given in GET operations (only possible operation) return all json data
        if not path:
            if operation == 'get':
                return json_data

            else:
                raise ValueError('path cannot be null in POST, PUT and DELETE operations')

        json_node_data = json_data

        last_json_node_data = None
        last_json_node_key = None
        for i in range(len(path)):
            key = path[i]

            if isinstance(json_node_data, list):
                try:
                    logger.debug(f'Trying to convert key \"{key}\" to an integer value because node is of type list...')
                    key = int(key)

                except ValueError:
                    # "json_node_data" contains a list and key is not an integer value,
                    # the key does not exist in the json
                    logger.warning(f'Key \"{key}\" does not exist in JSON data.')
                    raise KeyError(key)

            try:
                if i < len(path) - 1:
                    last_json_node_data, json_node_data = json_node_data, json_node_data[key]
                    last_json_node_key = key

                elif operation == 'post' or operation == 'put':
                    if isinstance(json_node_data[key], list):
                        # if an object already exists in the given index, replace that object with the new one
                        if isinstance(key, int):
                            logger.debug(f'Replacing value at the index \"{key}\" in list...')
                            json_node_data.pop(key)
                            json_node_data.insert(0, value)

                        else:
                            logger.debug(f'Appending value to list in \"{key}\"...')
                            json_node_data[key].append(value)

                    else:
                        logger.debug(f'Setting new value \"{value}\" to key \"{key}\"...')
                        json_node_data[key] = value

                elif operation == 'delete':
                    del json_node_data[key]

                else:
                    return json_node_data[key]

            except KeyError as key_error:
                if operation != 'post' and operation != 'put':
                    logger.warning(f'Key \"{key_error}\" does not exist in JSON data.')
                    raise key_error

                # creates a new node if it doesn't exist in the path or change the value from existing one
                json_node_data[key] = value if i == len(path) - 1 else dict()
                json_node_data = json_node_data[key]

            except TypeError:
                if operation != 'post' and operation != 'put':
                    # if "json_node_data" is the last node of the json then the remaining nodes in the path do not exist
                    raise KeyError(key)

                if not last_json_node_data:
                    last_json_node_data = dict()

                last_json_node_data[last_json_node_key] = dict()

                json_node_data = last_json_node_data[last_json_node_key]
                json_node_data[key] = value if i == len(path) - 1 else dict()

                last_json_node_data, json_node_data = json_node_data, json_node_data[key]

            except IndexError:
                # if the list has a smaller number of elements than the index given in the key,
                # then that element does not exist.
                raise KeyError(key)

    @staticmethod
    def publish_config(json_data: object, json_path_parts: List[str], json_file_path: str = None, path_depth: int = 0):
        """
        Publish the JSON data to broker using the "json_path_parts" as topic.
        If a path_depth is set the JSON json_path_parts will be shortened to that depth and the data will to be
        published is the data present in the resulting node.
        Example: If json_data = {node1: {node2: {node3: 'value'}}} json_path_parts = ['node1', 'node2', 'node3'] and
        path_depth = 1 the published message will be {"node2": {"node3": "value"}} to topic node1

        :param json_data: data object to publish (will be converted to JSON)
        :param json_path_parts: path parts, in the JSON, to the node, that will be used as topic
        :param json_file_path: Path or name of the JSON file where the operation was performed
        :param path_depth: sets the depth of the JSON path in json_path_parts.
               The published JSON data will be the ones existing in the node of that indicated depth.

        :return: True if message has been published, False if not
        """

        if path_depth > 0:
            json_path_parts = json_path_parts[:path_depth]

        if json_data is not None:  # can be an empty dict for example
            for part in json_path_parts:
                json_data = json_data[int(part)] if isinstance(json_data, list) else json_data[part]

            json_data = json.dumps(json_data)

        topic = ''

        # add json file name to MQTT topic or MQTT message body according to configurations
        if json_file_path:
            if CONFIG['mqtt']['publish']['request_file_in_message_content']:
                json_data = {
                    'file': json_file_path,
                    'json': json_data
                }

            else:
                topic += f'{json_file_path}/'

        topic += '/'.join(json_path_parts)
        if topic_prefix := CONFIG['mqtt']['publish']['topic_prefix']:
            topic = f'{topic_prefix}/{topic}'

        logger.debug(f'Publishing JSON data to \"{topic}\"...')
        if mqtt_client.is_connected():
            return mqtt_client.publish(topic, json_data, retain=True).is_published()

        return False

    @staticmethod
    def load_json_data(json_file_path: Union[str, Path]) -> object:
        """
        Read the JSON file and return the data as an object
        :param json_file_path: Path to the JSON file
        :return: Object
        """

        with open(json_file_path, 'r') as json_file_handler:
            return json.load(json_file_handler)

    def save_json_data(self,
                       json_data: object,
                       json_file_path: Union[str, Path],
                       json_schema_file_path: Union[str, Path] = None) -> None:
        """
        Save the object as JSON in the given file (creates the file if it doesn't exist)
        :param json_data: object to save as JSON
        :param json_file_path: Path to the JSON file
        :param json_schema_file_path: Path to the JSON schema
        """

        if json_schema_file_path:
            validate(json_data, self.load_json_data(json_schema_file_path))

        with open(json_file_path, 'w') as json_file_handler:
            json.dump(json_data, json_file_handler, indent=1)


def app():

    # set the default json file to be used
    for key, value in CONFIG['api']['files'].items():
        path = value['path']

        # load the file and schema (if defined) to ensure json integrity
        log_line_word = 'File'
        try:
            JsonHandler.load_json_data(path)

            if 'schema' in value and (path := value['schema']):
                log_line_word = 'Schema'
                JsonHandler.load_json_data(path)

        except json.JSONDecodeError as json_decode_error:
            logger.error(f'{log_line_word} \"{path}\" (specified at \"{key}\") has invalid JSON: '
                         f'{json_decode_error}')
            exit(1)

        except FileNotFoundError:
            logger.error(f'File \"{path}\" (specified at "{key}\") not found')
            exit(1)

        if value['default']:
            global DEFAULT_JSON_FILE
            DEFAULT_JSON_FILE = key

    # connect mqtt consumer if mqtt server is enabled
    if CONFIG['mqtt']['enabled']:
        mqtt_client.enable_logger(logger)

        # set the tls configuration
        if 'tls_config' in CONFIG['mqtt']:
            logger.debug(f'Setting up MQTT TLS configuration...')
            mqtt_client.tls_set(**CONFIG['mqtt']['tls_config'])

        # set the username and password
        if 'user' in CONFIG['mqtt']:
            logger.debug(f'Setting up MQTT username/password configuration...')
            mqtt_client.username_pw_set(**CONFIG['mqtt']['login'])

        logger.debug(f'MQTT client connecting to {CONFIG["mqtt"]["host"]}:{CONFIG["mqtt"]["port"]}...')
        try:
            mqtt_client.connect(CONFIG['mqtt']["host"], CONFIG['mqtt']["port"])

        except ConnectionRefusedError:
            logger.error(f'MQTT client connection to {CONFIG["mqtt"]["host"]}:{CONFIG["mqtt"]["port"]} refused.')
            exit(0)

        # start mqtt consumer
        mqtt_client.loop_start()
        logger.info('MQTT client successfully started.')

    # change default uvicorn log format
    uvicorn.config.LOGGING_CONFIG['formatters']['default']['fmt'] = \
        '%(asctime)s: [%(name)s] %(levelprefix)s %(message)s'

    # change access uvicorn log format
    uvicorn.config.LOGGING_CONFIG['formatters']['access']['fmt'] = \
        '%(asctime)s: [%(name)s] %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'

    return Starlette(routes=[
        Route('/{json_path:path}', JsonHandler, methods=['GET', 'POST', 'PUT', 'DELETE'])
    ])


if __name__ == '__main__':
    uvicorn.run("main:app")
