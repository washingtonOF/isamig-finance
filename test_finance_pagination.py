import unittest
from finance_pagination import collect_pages

class PaginationTests(unittest.TestCase):
    def test_multiple_pages(self):
        pages = {1: {"items":[{"id":"a"},{"id":"b"}]}, 2:{"items":[{"id":"c"}]}}
        self.assertEqual(len(collect_pages(lambda s,e,page:pages[page],"s","e","items",2)),3)
    def test_duplicate(self):
        with self.assertRaises(ValueError):
            collect_pages(lambda s,e,page:{"items":[{"id":"a"}]},"s","e","items",1)
    def test_invalid_schema(self):
        with self.assertRaises(ValueError):
            collect_pages(lambda s,e,page:{},"s","e","items",2)
    def test_limit(self):
        with self.assertRaises(ValueError):
            collect_pages(lambda s,e,page:{"items":[{"id":str(page)}]},"s","e","items",1,2)
    def test_empty(self):
        self.assertEqual(collect_pages(lambda s,e,page:{"items":[]},"s","e","items",2),[])
