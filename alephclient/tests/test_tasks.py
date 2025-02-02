import os

from alephclient.tasks.crawldir import crawl_dir
from alephclient.api import AlephAPI
from alephclient.util import Path


class TestCrawldir(object):
    def setup_method(self):
        self.api = AlephAPI(
            host="http://aleph.test/api/2/", api_key="fake_key"
        )

    def test_new_collection(self, mocker):
        mocker.patch.object(self.api, "filter_collections", return_value=[])
        mocker.patch.object(self.api, "create_collection")
        mocker.patch.object(self.api, "update_collection")
        mocker.patch.object(self.api, "ingest_upload")
        crawl_dir(self.api, "alephclient/tests/testdata", "test153", {})
        self.api.create_collection.assert_called_once_with({
            'category': 'other',
            'foreign_id': 'test153',
            'label': 'test153',
            'languages': [],
            'summary': '',
            'casefile': False
        })

    def test_ingest(self, mocker):
        mocker.patch.object(self.api, "ingest_upload",
                            return_value={"id": 42})
        mocker.patch.object(self.api, "load_collection_by_foreign_id",
                            return_value={"id": 2})
        mocker.patch.object(self.api, "update_collection")
        crawl_dir(self.api, "alephclient/tests/testdata", "test153", {})
        base_path = os.path.abspath("alephclient/tests/testdata")
        assert self.api.ingest_upload.call_count == 5
        expected_calls = [
            mocker.call(
                2,
                Path(os.path.join(base_path, "feb")),
                metadata={
                    'foreign_id': 'feb',
                    'file_name': 'feb'
                }
            ),
            mocker.call(
                2,
                Path(os.path.join(base_path, "jan")),
                metadata={
                    'foreign_id': 'jan',
                    'file_name': 'jan'
                }
            ),
            mocker.call(
                2,
                Path(os.path.join(base_path, "feb/2.txt")),
                metadata={
                    'parent_id': 42,
                    'foreign_id': 'feb/2.txt',
                    'file_name': '2.txt'
                }
            ),
            mocker.call(
                2,
                Path(os.path.join(base_path, "jan/week1")),
                metadata={
                    'parent_id': 42,
                    'foreign_id': 'jan/week1',
                    'file_name': 'week1'
                }
            ),
            mocker.call(
                2,
                Path(os.path.join(base_path, "jan/week1/1.txt")),
                metadata={
                    'parent_id': 42,
                    'foreign_id': 'jan/week1/1.txt',
                    'file_name': '1.txt'
                }
            ),
        ]
        for call in expected_calls:
            assert call in self.api.ingest_upload.mock_calls
