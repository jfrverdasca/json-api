# JSON files API

## Service description:
The purpose of the project is to allow CRUD (Create Read Update Delete) operations on JSON files through an API.
At the same time, the changes made are also published to a Mosquitto MQTT broker.

## Last service changes

* Config is now done with configuration file;
* MQTT broker TLS support
* MQTT broker login support
* Multiple file support
* Changes can now be validated with JSON schemas


## Service configuration:

Service configuration example:

```
{
  "mqtt": {
    "enabled": true,
    "host": "127.0.0.1",
    "port": 1883,
    "client_id": "<auto>",
    "publish": {
      "topic_prefix": "api/prefix",
      "json_path_topic_depth": 0,
      "request_file_in_message_content": false
    },
    "tls_config": <optional>
    "login": <optional>
  },
  "api": {
    "files": {
      "example": {
        "path": "example_file.json",
        "schema": "example_file_schema.json"
        "default": true
      },
      "other_example": {
        "path": "other_example_file.json"
      }
    }
  }
}
```

### MQTT configuration group:

#### enabled
**Type:** Boolean<br>
**Default:** true<br>
Enable or disable the MQTT service and the publication of messages.

#### host
**Type:** String<br>
**Default:** "127.0.0.1"<br>
Set the name or the ip of the MQTT server.

#### port
**Type:** Number<br>
**Default:** 1883<br>
Set the port of the MQTT server.

#### client_id
**Type:** String<br>
**Default:** "<auto>"<br>
Set the client id at the MQTT server. <auto> keyword will generate a random UUID.

#### publish/topic_prefix
**Type:** String<br>
Set the prefix of the topic to where messages are published as shown below:
<br><br>
API endpoint request:
```
http://.../node1/node2/
```
Topic to where updates will be published:
```
/<MQTT_TOPIC_PREFIX>/node1/node2
```

#### publish/json_path_topic_depth
**Type:** Number<br>
**Default:** 0<br>
Set the JSON path depth to use in the published MQTT topic as shown below (considering a depth of 2):
<br><br>
API endpoint request:
```
http://.../node1/node2/node3/node4
```
Topic to where updates will be published:
```
/<MQTT_TOPIC_PREFIX>/node1/node2
```

#### publish/request_file_in_message_content
**Type:** Boolean<br>
**Default:** False<br>
Set whether the name of the JSON file used in the API request should be placed in the body of the MQTT message.
<br><br>
If a file is specified and this option is disabled (false), the file used in the request at the API endpoint is 
specified in the MQTT topic as follows:
```
/<MQTT_TOPIC_PREFIX>/<file>/node1/node2
```
If a file is specified and this option is enabled, the message will be published with the following content:
```
{
    "file": "<json_file_name>",
    "json": ...
}
```

#### tls_config
Set the MQTT broker TLS (MQTTS) configuration as shown bellow:<bn>
```
"tls_config": {
    "ca_certs": path to Certificate Authority certificate files that are to be treated as trusted by this client,
    "certfile": path to the PEM encoded client certificate (optional),
    "keyfile": path to the client private key file (optional),
    "cert_reqs":  defines the certificate requirements that the client imposes on the broker (optional, valid values are "none", "optional" and "required", default "required"),
    "tls_version": specifies the version of the TLS protocol to be used (optional, valid values are 1, 1.1 and 1.2, default 1.2),
    "ciphers": string specifying which encryption ciphers are allowable for this connection (optional, empty to use defaults)
    "keyfile_password": string password of the private key file (optional, can be a path to a file to use with Docker Secrets)
}
```
See the "tls_set()" option in this [page](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#option-functions) to more detailed information about each field.

#### login
Set the MQTT broker login configuration as shown bellow:<br>
```
"login": {
    "username": broker username,
    "password": broker password
}
```


### API configuration group:

#### files group:

#### <name that should be used in request>
The name set in here must be used in the API endpoint for the file specified in this group to be used as shown below:
```
http://.../<json_file_name>/node1/node2/...
```

#### path
**Type:** String<br>
Set the JSON file path to be used

#### schema
**Type:** String<br>
Set the JSON schema file to be used to validate the file set in the "path" configuration

#### default
**Type:** String<br>
Set which file should be used if none is specified in the request to the API endpoint

**NOTES:** 

* If several files are configured as default, the **last** file in the list of files with default as true will 
be considered;
* If none of the files is defined as the default, the **first** one defined will be used as the default.


## Environment variables:
To allow a correct execution of the project some environment variables must be defined:

* LOGGING_LEVEL: Sets the logging level value. Lower values, more detailed logs (default: 20 (INFO));
* CONFIG: Sets the path to the service configuration file (default: config.json).


## How to run

### Using docker:
Simply go to the directory where the project was cloned from git and do:<br>
```
$ docker-compose up -d
```

### Outside of docker container:
**Instructions for Linux. On Windows or OSX the commands may vary**<br>
<br>
First, set the environment variables described in [Initial Requirements](#initial-requirements)<br>
Go to the directory where the project was cloned from git and do:<br>
```
$ python3 -m venv ./venv
$ source ./venv/bin/activate
$ pip3 install -r server/requirements.txt
$ uvicorn main:app --host 0.0.0.0 --port 8000
```

## Allowed operations:
* **GET**: Get the value of the JSON node to the given path
* **POST** (or **PUT**): Add new nodes to the JSON structure or change the value of existing ones
* **DELETE**: Delete the node in the given path

## Examples
**IMPORTANT NOTES:** 

* Keep in mind that all provided examples assume the default values for all environment variables;
* The examples assume **only one JSON file is being used by the API**.

Considering the following JSON content:
```
{
    "node1": {
        "node11": "value11",
        "node12": [
            {"id": 0}, 
            {"id": 1}, 
            {"id": 2}, 
            {"id": 3}
            ],
        "node13": {
            "node111": "value111"
        }
    },
    "node2": "value2"
}
```

* [Create](#create)
* [Read](#read)
* [Update](#update)
* [Delete](#delete)

### CREATE
* Create requests must have a JSON body with the desired content for new nodes
* Create operations that have no content in the response, just respond with HTTP code **200** if the request is successful or 
any other HTTP code in case of an error
* **Create operations does not return HTTP code 404**. Non-existing nodes will be created.
* **Create operations in root path (http://.../) will replace all file content**


#### Create a new node
**Method**: POST (or PUT)<br>
**Endpoint**: http://.../new_node<br>
**Request content**:
```
{"data": 0}
```

New JSON structure:
```
{
    "node1": {
        "node11": "value11",
        "node12": [
            {"id": 0}, 
            {"id": 1}, 
            {"id": 2}, 
            {"id": 3}
            ],
        "node13": {
            "node111": "value111"
        }
    },
    "node2": "value2",
    "new_node": {"data": 0}
}
```

#### Create multiple new nodes
**Method**: POST (or PUT)<br>
**Endpoint**: http://.../new_node1/new_node2<br>
**Request content**:
```
{"data": 0}
```

New JSON structure:
```
{
    "node1": {
        "node11": "value11",
        "node12": [
            {"id": 0}, 
            {"id": 1}, 
            {"id": 2}, 
            {"id": 3}
            ],
        "node13": {
            "node111": "value111"
        }
    },
    "node2": "value2",
    "new_node1": {
        "new_node2": {"data": 0}
    }
}
```

#### Append new value to a node list
**Method**: POST (or PUT)<br>
**Endpoint**: http://.../node1/node12<br>
**Request content**:
```
{"id": 4}
```

New JSON structure:
```
{
    "node1": {
        "node11": "value11",
        "node12": [
            {"id": 0}, 
            {"id": 1}, 
            {"id": 2}, 
            {"id": 3},
            {"id": 4}
            ],
        "node13": {
            "node111": "value111"
        }
    },
    "node2": "value2"
}
```

### READ
* Read operations respond with the content of the JSON node given in the endpoint
* Read operations respond with HTTP code **404** if the node does not exist in JSON structure or does not exist in a list inside a node

#### Read the entire JSON
**Method**: GET<br>
**Endpoint**: http://.../<br>

Response:
```
{
    "node1": {
        "node11": "value11",
        "node12": [
            {"id": 0}, 
            {"id": 1}, 
            {"id": 2}, 
            {"id": 3},
            {"id": 4}
            ],
        "node13": {
            "node111": "value111"
        }
    },
    "node2": "value2"
}
```

#### Read the value of simple node
**Method**: GET<br>
**Endpoint**: http://.../node1/node11<br>

Response:
```
"value11"
```

#### Read the value of a node list
**Method**: GET<br>
**Endpoint**: http://.../node1/node12/3/id<br>

Response:
```
3
```

### UPDATE
* Update requests must have a JSON body with the desired content for updated nodes
* Update operations have no content in the response, just respond with HTTP code **200** if the request is successful 
or any other HTTP code in case of an error
* **Update operations do not return HTTP code 404**. Non-existing nodes will be created.

#### Update the value of a node
**Method**: POST (or PUT)<br>
**Endpoint**: http://.../node1/node11<br>
**Request content**:
```
"new_value11"
```

New JSON structure:
```
{
    "node1": {
        "node11": "new_value11",
        "node12": [
            {"id": 0}, 
            {"id": 1}, 
            {"id": 2}, 
            {"id": 3},
            {"id": 4}
            ],
        "node13": {
            "node111": "value111"
        }
    },
    "node2": "value2"
}
```

#### Update the value of a node with a new node
**Method**: POST (or PUT)<br>
**Endpoint**: http://.../node1/node11/node111<br>
**Request content**:
```
"value111"
```

OR

**Method**: POST (or PUT)<br>
**Endpoint**: http://.../node1/node11<br>
**Request content**:
```
{"node111": "value111"}
```

New JSON structure:
```
{
    "node1": {
        "node11": {
            "node111": "value111"
        },
        "node12": [
            {"id": 0}, 
            {"id": 1}, 
            {"id": 2}, 
            {"id": 3},
            {"id": 4}
            ],
        "node13": {
            "node111": "value111"
        }
    },
    "node2": "value2"
}
```

#### Update a value from a node with a list
**Method**: POST (or PUT)<br>
**Endpoint**: http://.../node1/node12/1<br>
**Request content**:
```
{"id": 5}
```

New JSON structure:
```
{
    "node1": {
        "node11": "new_value11",
        "node12": [
            {"id": 0}, 
            {"id": 5}, 
            {"id": 2}, 
            {"id": 3},
            {"id": 4}
            ],
        "node13": {
            "node111": "value111"
        }
    },
    "node2": "value2"
}
```

### DELETE
* Delete operations that have no content in the response, just respond with HTTP code **200** if the request is successful 
or any other HTTP code in case of an error
* Read operations respond with HTTP code **404** if the node does not exist in JSON structure or does not exist in a list inside a node
* **Delete operations not possible at root path (http://.../)**

#### Delete a node
**Method**: DELETE<br>
**Endpoint**: http://.../node1/node11

New JSON structure:
```
{
    "node1": {
        "node12": [
            {"id": 0}, 
            {"id": 1}, 
            {"id": 2}, 
            {"id": 3},
            {"id": 4}
            ],
        "node13": {
            "node111": "value111"
        }
    },
    "node2": "value2"
}
```

#### Delete a node with sub-nodes
**Method**: DELETE<br>
**Endpoint**: http://.../node13

New JSON structure:
```
{
    {
    "node1": {
        "node11": "new_value11",
        "node12": [
            {"id": 0}, 
            {"id": 1}, 
            {"id": 2}, 
            {"id": 3},
            {"id": 4}
            ],
    },
    "node2": "value2"
}
```

#### Delete a value from a node with a list
**Method**: DELETE<br>
**Endpoint**: http://.../node1/node12/2

New JSON structure:
```
{
    "node1": {
        "node11": "value11",
        "node12": [
            {"id": 0}, 
            {"id": 1}, 
            {"id": 3}
            ],
        "node13": {
            "node111": "value111"
        }
    },
    "node2": "value2"
}
```

## Other response errors:
* Requests with incorrect URLs (like http://.../test///) will return HTTP **400** code
* HTTP **500** code can occur if, for example, the JSON file is malformed
