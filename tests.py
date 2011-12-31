# -*- coding: utf-8 -*-
"""
Unit tests for pyelasticsearch.  These require an elasticsearch server running on the default port (localhost:9200).
"""
import datetime
import logging
import unittest
from pyelasticsearch import ElasticSearch


class VerboseElasticSearch(ElasticSearch):
     def setup_logging(self):
         log = super(VerboseElasticSearch, self).setup_logging()
         log.setLevel(logging.DEBUG)
         return log


class ElasticSearchTestCase(unittest.TestCase):
    def setUp(self):
        self.conn = ElasticSearch('http://localhost:9200/')

    def tearDown(self):
        self.conn.delete_index("test-index")

    def assertResultContains(self, result, expected):
        for (key, value) in expected.items():
            self.assertEquals(value, result[key])


class IndexingTestCase(ElasticSearchTestCase):
    def testSetupLogging(self):
        log = self.conn.setup_logging()
        self.assertTrue(isinstance(log, logging.Logger))
        self.assertEqual(log.level, logging.ERROR)

    def testOverriddenSetupLogging(self):
        conn = VerboseElasticSearch('http://localhost:9200/')
        log = conn.setup_logging()
        self.assertTrue(isinstance(log, logging.Logger))
        self.assertEqual(log.level, logging.DEBUG)

    def testIndexingWithID(self):
        result = self.conn.index({"name":"Joe Tester"}, "test-index", "test-type", 1)
        self.assertResultContains(result, {'_type': 'test-type', '_id': '1', 'ok': True, '_index': 'test-index'} )

    def testIndexingWithoutID(self):
        result = self.conn.index({"name":"Joe Tester"}, "test-index", "test-type")
        self.assertResultContains(result, {'_type': 'test-type', 'ok': True, '_index': 'test-index'} )
        # should have an id of some value assigned.
        self.assertTrue(result.has_key('_id') and result['_id'])

    def testExplicitIndexCreate(self):
        result = self.conn.create_index("test-index")
        self.assertResultContains(result, {'acknowledged': True, 'ok': True})

    def testDeleteByID(self):
        self.conn.index({"name":"Joe Tester"}, "test-index", "test-type", 1)
        self.conn.refresh(["test-index"])
        result = self.conn.delete("test-index", "test-type", 1)
        self.assertResultContains(result, {'_type': 'test-type', '_id': '1', 'ok': True, '_index': 'test-index'})

    def testDeleteByQuery(self):
        self.conn.index({"name":"Joe Tester"}, "test-index", "test-type", 1)
        self.conn.index({"name":"Bill Baloney"}, "test-index", "test-type", 2)
        self.conn.index({"name":"Horace Humdinger"}, "test-index", "test-type", 3)
        self.conn.refresh(["test-index"])

        self.conn.refresh(["test-index"])
        result = self.conn.count("*:*", indexes=['test-index'])
        self.assertResultContains(result, {'count': 3})

        result = self.conn.delete_by_query("test-index", "test-type", {"query_string": {"query": "name:joe OR name:bill"}})
        self.assertResultContains(result, {'ok': True})

        self.conn.refresh(["test-index"])
        result = self.conn.count("*:*", indexes=['test-index'])
        self.assertResultContains(result, {'count': 1})

    def testDeleteIndex(self):
        self.conn.create_index("another-index")
        result = self.conn.delete_index("another-index")
        self.assertResultContains(result, {'acknowledged': True, 'ok': True})

    def testCannotCreateExistingIndex(self):
        self.conn.create_index("another-index")
        result = self.conn.create_index("another-index")
        self.conn.delete_index("another-index")
        self.assertResultContains(result, {'error': '[another-index] Already exists'})

    def testPutMapping(self):
        result = self.conn.create_index("test-index")
        result = self.conn.put_mapping("test-type", {"test-type" : {"properties" : {"name" : {"type" : "string", "store" : "yes"}}}}, indexes=["test-index"])
        self.assertResultContains(result, {'acknowledged': True, 'ok': True})

    def testIndexStatus(self):
        self.conn.create_index("another-index")
        result = self.conn.status(["another-index"])
        self.conn.delete_index("another-index")
        self.assertTrue(result.has_key('indices'))
        self.assertResultContains(result, {'ok': True})

    def testIndexFlush(self):
        self.conn.create_index("another-index")
        result = self.conn.flush(["another-index"])
        self.conn.delete_index("another-index")
        self.assertResultContains(result, {'ok': True})

    def testIndexRefresh(self):
        self.conn.create_index("another-index")
        result = self.conn.refresh(["another-index"])
        self.conn.delete_index("another-index")
        self.assertResultContains(result, {'ok': True})

    def testIndexOptimize(self):
        self.conn.create_index("another-index")
        result = self.conn.optimize(["another-index"])
        self.conn.delete_index("another-index")
        self.assertResultContains(result, {'ok': True})

    def testFromPython(self):
        self.assertEqual(self.conn.from_python('abc'), u'abc')
        self.assertEqual(self.conn.from_python(u'☃'), u'☃')
        self.assertEqual(self.conn.from_python(123), 123)
        self.assertEqual(self.conn.from_python(12.2), 12.2)
        self.assertEqual(self.conn.from_python(True), True)
        self.assertEqual(self.conn.from_python(False), False)
        self.assertEqual(self.conn.from_python(datetime.date(2011, 12, 30)), '2011-12-30T00:00:00')
        self.assertEqual(self.conn.from_python(datetime.datetime(2011, 12, 30, 11, 59, 32)), '2011-12-30T11:59:32')
        self.assertEqual(self.conn.from_python([1, 2, 3]), [1, 2, 3])
        self.assertEqual(self.conn.from_python(set(['a', 'b', 'c'])), set(['a', 'b', 'c']))
        self.assertEqual(self.conn.from_python({'a': 1, 'b': 3, 'c': 2}), {'a': 1, 'b': 3, 'c': 2})

    def testToPython(self):
        self.assertEqual(self.conn.to_python(u'abc'), u'abc')
        self.assertEqual(self.conn.to_python(u'☃'), u'☃')
        self.assertEqual(self.conn.to_python(123), 123)
        self.assertEqual(self.conn.to_python(12.2), 12.2)
        self.assertEqual(self.conn.to_python(True), True)
        self.assertEqual(self.conn.to_python(False), False)
        self.assertEqual(self.conn.to_python('2011-12-30T00:00:00'), datetime.datetime(2011, 12, 30))
        self.assertEqual(self.conn.to_python('2011-12-30T11:59:32'), datetime.datetime(2011, 12, 30, 11, 59, 32))
        self.assertEqual(self.conn.to_python([1, 2, 3]), [1, 2, 3])
        self.assertEqual(self.conn.to_python(set(['a', 'b', 'c'])), set(['a', 'b', 'c']))
        self.assertEqual(self.conn.to_python({'a': 1, 'b': 3, 'c': 2}), {'a': 1, 'b': 3, 'c': 2})

    def testBulkIndex(self):
        docs = [
            {"name":"Joe Tester"},
            {"name":"Bill Baloney", "id": 303},
        ]
        result = self.conn.bulk_index("test-index", "test-type", docs)
        self.assertResultContains(result, {u'_type': u'test-type', u'_id': u'_bulk', u'ok': True, u'_index': u'test-index'})


class SearchTestCase(ElasticSearchTestCase):
    def setUp(self):
        super(SearchTestCase, self).setUp()
        self.conn.index({"name":"Joe Tester"}, "test-index", "test-type", 1)
        self.conn.index({"name":"Bill Baloney"}, "test-index", "test-type", 2)
        self.conn.refresh(["test-index"])

    def testGetByID(self):
        result = self.conn.get("test-index", "test-type", 1)
        self.assertResultContains(result, {'_type': 'test-type', '_id': '1', '_source': {'name': 'Joe Tester'}, '_index': 'test-index'})

    def testGetCountBySearch(self):
        result = self.conn.count("name:joe")
        self.assertResultContains(result, {'count': 1})

    def testSearchByField(self):
        result = self.conn.search("name:joe")
        self.assertResultContains(result, {'hits': {'hits': [{'_type': 'test-type', '_id': '1', '_source': {'name': 'Joe Tester'}, '_index': 'test-index'}], 'total': 1}})

    def testTermsByField(self):
        result = self.conn.terms(['name'])
        self.assertResultContains(result, {'docs': {'max_doc': 2, 'num_docs': 2, 'deleted_docs': 0}, 'fields': {'name': {'terms': [{'term': 'baloney', 'doc_freq': 1}, {'term': 'bill', 'doc_freq': 1}, {'term': 'joe', 'doc_freq': 1}, {'term': 'tester', 'doc_freq': 1}]}}})

    def testTermsByIndex(self):
        result = self.conn.terms(['name'], indexes=['test-index'])
        self.assertResultContains(result, {'docs': {'max_doc': 2, 'num_docs': 2, 'deleted_docs': 0}, 'fields': {'name': {'terms': [{'term': 'baloney', 'doc_freq': 1}, {'term': 'bill', 'doc_freq': 1}, {'term': 'joe', 'doc_freq': 1}, {'term': 'tester', 'doc_freq': 1}]}}})

    def testTermsMinFreq(self):
        result = self.conn.terms(['name'], min_freq=2)
        self.assertResultContains(result, {'docs': {'max_doc': 2, 'num_docs': 2, 'deleted_docs': 0}, 'fields': {'name': {'terms': []}}})

    def testMLT(self):
        self.conn.index({"name":"Joe Test"}, "test-index", "test-type", 3)
        self.conn.refresh(["test-index"])
        result = self.conn.morelikethis("test-index", "test-type", 1, ['name'], min_term_freq=1, min_doc_freq=1)
        self.assertResultContains(result, {'hits': {'hits': [{'_type': 'test-type', '_id': '3', '_source': {'name': 'Joe Test'}, '_index': 'test-index'}], 'total': 1}})


if __name__ == "__main__":
    unittest.main()