import os
import unittest.mock
import urllib.error
import string
import random
import pkg_resources
from pychado import dbutils


class TestConnection(unittest.TestCase):
    """Tests for database connections"""

    def setUp(self):
        # Checks if the default connection file is available and reads in the parameters
        self.assertTrue(os.path.exists(os.path.abspath(dbutils.default_configuration_file())))
        self.connectionParameters = dbutils.read_configuration_file("")
        self.dsn = dbutils.generate_dsn(self.connectionParameters)

    def tearDown(self):
        self.connectionParameters.clear()

    def test_connection_parameters(self):
        # Tests if the default connection file contains all required parameters
        self.assertIn("database", self.connectionParameters)
        self.assertIn("user", self.connectionParameters)
        self.assertIn("password", self.connectionParameters)
        self.assertIn("host", self.connectionParameters)
        self.assertIn("port", self.connectionParameters)

    def test_connection_uri(self):
        # Tests the correct creation of a database connection string in URI format
        uri = "postgresql://" \
              + self.connectionParameters["user"] + ":" \
              + self.connectionParameters["password"] + "@" \
              + self.connectionParameters["host"] + ":" \
              + self.connectionParameters["port"] + "/" \
              + self.connectionParameters["database"]
        self.assertEqual(dbutils.generate_uri(self.connectionParameters), uri)

    def test_connection_dsn(self):
        # Tests the correct creation of a database connection string in keyword/value format
        dsn = "dbname=" + self.connectionParameters["database"] \
              + " user=" + self.connectionParameters["user"] \
              + " password=" + self.connectionParameters["password"] \
              + " host=" + self.connectionParameters["host"] \
              + " port=" + self.connectionParameters["port"]
        self.assertEqual(dbutils.generate_dsn(self.connectionParameters), dsn)

    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", "Skipping this test on Travis CI.")
    def test_connect(self):
        # Tests that a connection to the default database can be established and that queries can be executed
        result = dbutils.connect_and_execute_query(self.dsn, "SELECT 1 + 2")
        self.assertEqual(result[0][0], 3)

    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", "Skipping this test on Travis CI.")
    def test_exists(self):
        # Test the "exists" function by checking for existence of the obligatory template0 database
        self.assertTrue(dbutils.exists(self.dsn, "template0"))

    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", "Skipping this test on Travis CI.")
    def test_create_drop_dump_restore(self):
        # Test the basic functionality for creation and deletion of databases
        # NOTE: This test depends on an example SQL schema in the tests/data directory.
        # If the schema is changed, the test might fail.

        # Generate a random database name
        dbname = "template0"
        while dbutils.exists(self.dsn, dbname):
            dbname = ''.join(random.choices(string.ascii_lowercase, k=20))
        parameters = self.connectionParameters.copy()
        parameters["database"] = dbname
        uri = dbutils.generate_uri(parameters)
        dsn = dbutils.generate_dsn(parameters)

        # Create the database and check it exists
        dbutils.create_database(self.dsn, dbname)
        self.assertTrue(dbutils.exists(self.dsn, dbname))

        # Set up the database according to a test schema
        testSchema = pkg_resources.resource_filename("pychado", "tests/data/dbutils_example_schema.sql")
        self.assertTrue(os.path.exists(os.path.abspath(testSchema)))
        dbutils.setup_database(uri, testSchema)

        # Check if the database is correctly set up
        result = dbutils.connect_and_execute_query(dsn, "SELECT * FROM species ORDER BY legs ASC")
        self.assertEqual(len(result), 4)
        self.assertIn("leech", result[0])

        # Dump the database and check for the archive file
        archiveFile = "tmp.dump"
        dbutils.dump_database(uri, archiveFile)
        self.assertTrue(os.path.exists(os.path.abspath(archiveFile)))

        # Restore the database and check it exists
        dbutils.restore_database(uri, archiveFile)
        self.assertTrue(dbutils.exists(self.dsn, dbname))

        # Check if the database is still correctly set up
        result = dbutils.connect_and_execute_query(dsn, "SELECT name FROM species WHERE extinct = TRUE")
        self.assertEqual(len(result), 1)
        self.assertEqual("diplodocus", result[0][0])

        # Drop the database, remove the archive file and check that everything is gone
        dbutils.drop_database(self.dsn, dbname)
        self.assertFalse(dbutils.exists(self.dsn, dbname))
        os.remove(os.path.abspath(archiveFile))
        self.assertFalse(os.path.exists(os.path.abspath(archiveFile)))


class TestDownload(unittest.TestCase):
    """Tests for data download"""

    def test_default_schema_url(self):
        # Tests if the default schema is retrievable and has a valid address
        url = dbutils.default_schema_url()
        self.assertEqual(url[:4], "http")
        self.assertEqual(url[-3:], "sql")

    def test_download_schema(self):
        # Tests the download of a file from a given url
        url = dbutils.default_schema_url()
        dbutils.download_schema(url)
        url = url + "_arbitraryString"
        with self.assertRaises(urllib.error.HTTPError):
            dbutils.download_schema(url)
        url = "http://xyzxyz.xyzxyz"
        with self.assertRaises(urllib.error.URLError):
            dbutils.download_schema(url)


if __name__ == '__main__':
    unittest.main(buffer=True)