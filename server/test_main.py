from unittest import TestCase

from httpx import Client, Request

import json

from pathlib import Path
from shutil import copy2


class TestJsonHandler(TestCase):

    def setUp(self) -> None:
        # set files to its original values
        copy2('../test_config/example.json', 'example.json')
        copy2('../test_config/other_example.json', 'other_example.json')

    # def tearDown(self) -> None:
    #     # clean test files
    #     Path('example.json').unlink()
    #     Path('other_example.json').unlink()

    def test_create_new_node_in_existing_node(self):
        request_content = {'data': 0}

        try:
            with Client() as client:
                response = client.send(Request(method='PUT',
                                               url='http://localhost:8000/node1/test',
                                               content=json.dumps(request_content)))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.content, b'')

        except Exception as e:
            self.fail(e)

        else:
            value = self.get_json_value('node1/test')
            self.assertEqual(value, request_content, f'Value mismatch')

    def test_create_new_node_new_node(self):
        request_content = {'data': 0}

        try:
            with Client() as client:
                response = client.send(Request(method='PUT',
                                               url='http://localhost:8000/test/test',
                                               content=json.dumps(request_content)))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.content, b'')

        except Exception as e:
            self.fail(e)

        else:
            value = self.get_json_value('test/test')
            self.assertEqual(value, request_content, f'Value mismatch')

    def test_append_value_node_with_list(self):
        request_content = {'data': 0}

        try:
            with Client() as client:
                response = client.send(Request(method='PUT',
                                               url='http://localhost:8000/node2/list',
                                               content=json.dumps(request_content)))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.content, b'')

        except Exception as e:
            self.fail(e)

        else:
            value = len(self.get_json_value('node2/list'))
            self.assertEqual(value, 3, f'Value mismatch')

    def test_create_node_other_example_file(self):
        request_content = {'data': 0}

        try:
            with Client() as client:
                response = client.send(Request(method='PUT',
                                               url='http://localhost:8000/other_example.json/node2/innerNode23',
                                               content=json.dumps(request_content)))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.content, b'')

        except Exception as e:
            self.fail(e)

        else:
            value = self.get_json_value('node2/innerNode23', 'other_example.json')
            self.assertEqual(value, request_content, f'Value mismatch')

    def test_read_node_value(self):
        value = self.get_json_value('node3/innerNode31')

        try:
            with Client() as client:
                response = client.send(Request(method='GET',
                                               url='http://localhost:8000/node3/innerNode31'))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.json(), value)

        except Exception as e:
            self.fail(e)

    def test_read_node_list_value(self):
        value = self.get_json_value('node2/list/0')

        try:
            with Client() as client:
                response = client.send(Request(method='GET',
                                               url='http://localhost:8000/node2/list/0'))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.json(), value)

        except Exception as e:
            self.fail(e)

    def test_read_node_list_out_of_range(self):
        try:
            with Client() as client:
                response = client.send(Request(method='GET',
                                               url='http://localhost:8000/node2/list/100'))

                self.assertTrue(response.status_code == 404, f'Unexpected status code: {response.status_code}')

        except Exception as e:
            self.fail(e)

    def test_read_node_other_example_file(self):
        value = self.get_json_value('node2/innerNode21', 'other_example.json')

        try:
            with Client() as client:
                response = client.send(Request(method='GET',
                                               url='http://localhost:8000/other_example.json/node2/innerNode21'))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.json(), value)

        except Exception as e:
            self.fail(e)

    def test_update_value_file_to_node(self):
        # change file content to just a value
        with open('example.json', 'wt') as json_file_handler:
            json_file_handler.write('0')

        value = self.get_json_value()
        self.assertEqual(value, 0, f'Value mismatch')

        request_content = {'data': 0}

        try:
            with Client() as client:
                response = client.send(Request(method='PUT',
                                               url='http://localhost:8000/',
                                               content=json.dumps(request_content)))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.content, b'')

        except Exception as e:
            self.fail(e)

        else:
            value = self.get_json_value()
            self.assertEqual(value, request_content, f'Value mismatch')

    def test_update_value_file_to_node_1(self):
        # change file content to just a value
        with open('example.json', 'wt') as json_file_handler:
            json_file_handler.write('0')

        value = self.get_json_value()
        self.assertEqual(value, 0, f'Value mismatch')

        request_content = {'data': 0}

        try:
            with Client() as client:
                response = client.send(Request(method='PUT',
                                               url='http://localhost:8000/file/value/content',
                                               content=json.dumps(request_content)))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.content, b'')

        except Exception as e:
            self.fail(e)

        else:
            value = self.get_json_value('file/value/content')
            self.assertEqual(value, request_content, f'Value mismatch')

    def test_update_value_other_example_file(self):
        request_content = 'new_node1_value'

        try:
            with Client() as client:
                response = client.send(Request(method='PUT',
                                               url='http://localhost:8000/other_example.json/node1',
                                               content=json.dumps(request_content)))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.content, b'')

        except Exception as e:
            self.fail(e)

        else:
            value = self.get_json_value('node1', 'other_example.json')
            self.assertEqual(value, request_content, f'Values mismatch')

    def test_read_node_value_404(self):
        try:
            with Client() as client:
                response = client.send(Request(method='GET',
                                               url='http://localhost:8000/test/nonexistent_node'))

                self.assertTrue(response.status_code == 404, f'Unexpected status code: {response.status_code}')

        except Exception as e:
            self.fail(e)

    def test_update_node_value(self):
        request_content = 'new_node3_value'

        try:
            with Client() as client:
                response = client.send(Request(method='POST',
                                               url='http://localhost:8000/node3/innerNode31',
                                               content=json.dumps(request_content)))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.content, b'')

        except Exception as e:
            self.fail(e)

        else:
            value = self.get_json_value('node3/innerNode31')
            self.assertEqual(value, request_content, f'Value mismatch')

    def test_update_node_value_new_node(self):
        request_content = {'value1': 'new_value_1',
                           'value2': 'new_value_2'}

        try:
            with Client() as client:
                response = client.send(Request(method='POST',
                                               url='http://localhost:8000/node1/test',
                                               content=json.dumps(request_content)))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.content, b'')

        except Exception as e:
            self.fail(e)

        else:
            value = self.get_json_value('node1/test')
            self.assertEqual(value, request_content, f'Value mismatch')

    def test_update_node_value_new_node_1(self):
        request_content = 'new_value_1'

        try:
            with Client() as client:
                response = client.send(Request(method='POST',
                                               url='http://localhost:8000/node1/test_1',
                                               content=json.dumps(request_content)))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.content, b'')

        except Exception as e:
            self.fail(e)

        else:
            value = self.get_json_value('node1/test_1')
            self.assertEqual(value, request_content, f'Value mismatch')

    def test_update_node_value_new_node_new_node(self):
        request_content = {'value1': 'new_value_1',
                           'value2': 'new_value_2'}

        try:
            with Client() as client:
                response = client.send(Request(method='POST',
                                               url='http://localhost:8000/node1/test_1/test_2',
                                               content=json.dumps(request_content)))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.content, b'')

        except Exception as e:
            self.fail(e)

        else:
            value = self.get_json_value('node1/test_1/test_2')
            self.assertEqual(value, request_content, f'Value mismatch')

    def test_update_node_list_value(self):
        request_content = {'data': 0}

        try:
            with Client() as client:
                response = client.send(Request(method='POST',
                                               url='http://localhost:8000/node2/list/0',
                                               content=json.dumps(request_content)))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.content, b'')

        except Exception as e:
            self.fail(e)

        else:
            value = self.get_json_value('node2/list/0')
            self.assertEqual(value, request_content, f'Value mismatch')

    def test_delete_node(self):
        try:
            with Client() as client:
                response = client.send(Request(method='DELETE',
                                               url='http://localhost:8000/node3/innerNode31'))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.content, b'')

        except Exception as e:
            self.fail(e)

        else:
            self.assertRaisesRegex(KeyError, 'innerNode31', self.get_json_value, 'node3/innerNode31')

    def test_delete_sub_nodes(self):
        try:
            with Client() as client:
                response = client.send(Request(method='DELETE',
                                               url='http://localhost:8000/node1'))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.content, b'')

        except Exception as e:
            self.fail(e)

        else:
            self.assertRaisesRegex(KeyError, 'node1', self.get_json_value, 'node1')

    def test_delete_node_list_value(self):
        try:
            with Client() as client:
                response = client.send(Request(method='DELETE',
                                               url='http://localhost:8000/node2/list/0'))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.content, b'')

        except Exception as e:
            self.fail(e)

        else:
            value = len(self.get_json_value('node2/list'))
            self.assertEqual(value, 1, f'Value mismatch')

    def test_delete_node_other_example_file(self):
        try:
            with Client() as client:
                response = client.send(Request(method='DELETE',
                                               url='http://localhost:8000/other_example.json/node2'))

                self.assertTrue(response.status_code == 200, f'Unexpected status code: {response.status_code}')
                self.assertEqual(response.content, b'')

        except Exception as e:
            self.fail(e)

        else:
            self.assertRaisesRegex(KeyError, 'node2', self.get_json_value, 'node2', 'other_example.json')

    def test_delete_node_404(self):
        try:
            with Client() as client:
                response = client.send(Request(method='DELETE',
                                               url='http://localhost:8000/node1/innerNode11'))

                self.assertTrue(response.status_code == 404, f'Unexpected status code: {response.status_code}')
                self.assertTrue(response.content, b'')

        except Exception as e:
            self.fail(e)

    def test_delete_all_nodes(self):
        try:
            with Client() as client:
                response = client.send(Request(method='DELETE',
                                               url='http://localhost:8000/'))

                self.assertTrue(response.status_code == 400, f'Unexpected status code: {response.status_code}')
                self.assertTrue(response.content, b'')

        except Exception as e:
            self.fail(e)
            
    def test_delete_file_value(self):
        # change file content to just a value
        with open('example.json', 'wt') as json_file_handler:
            json_file_handler.write('0')

        value = self.get_json_value()
        self.assertEqual(value, 0, f'Value mismatch')
        
        try:
            with Client() as client:
                response = client.send(Request(method='DELETE',
                                               url='http://localhost:8000/'))
                
                self.assertTrue(response.status_code == 400, f'Unexpected status code: {response.status_code}')

        except Exception as e:
            self.fail(e)

    def test_delete_file_value_1(self):
        # change file content to just a value
        with open('example.json', 'wt') as json_file_handler:
            json_file_handler.write('0')

        value = self.get_json_value()
        self.assertEqual(value, 0, f'Value mismatch')

        try:
            with Client() as client:
                response = client.send(Request(method='DELETE',
                                               url='http://localhost:8000/file/value/content'))

                self.assertTrue(response.status_code == 404, f'Unexpected status code: {response.status_code}')

        except Exception as e:
            self.fail(e)

    def test_invalid_url(self):
        try:
            with Client() as client:
                response = client.send(Request(method='GET',
                                               url='http://localhost:8000/general/network///'))

                self.assertTrue(response.status_code == 400, f'Unexpected status code: {response.status_code}')

        except Exception as e:
            self.fail(e)

    def test_invalid_url_1(self):
        try:
            with Client() as client:
                response = client.send(Request(method='GET',
                                               url='http://localhost:8000/general/net work/'))

                self.assertTrue(response.status_code == 400, f'Unexpected status code: {response.status_code}')

        except Exception as e:
            self.fail(e)

    @staticmethod
    def get_json_value(path='', json_file='example.json'):
        with open(json_file, 'r') as json_file_handler:
            json_data = json.load(json_file_handler)

        if path:
            for key in path.split('/'):
                if isinstance(json_data, list):
                    try:
                        key = int(key)

                    except ValueError:
                        pass

                json_data = json_data[key]

        return json_data
