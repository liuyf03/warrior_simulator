import unittest
import sys

def run_all_tests():
    """
    Discovers and runs all unit tests located in the 'unittests' directory.
    """
    print("--- Discovering and running all unit tests ---")
    
    # Define the directory where your tests are located
    test_directory = 'unittests'
    
    # Create a TestLoader instance
    loader = unittest.TestLoader()
    
    # Discover all tests in the specified directory.
    # The default pattern 'test*.py' will find all your test files.
    suite = loader.discover(test_directory)
    
    # Create a TextTestRunner to execute the tests and display results.
    # verbosity=2 provides more detailed output for each test.
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with a non-zero status code if any tests failed, useful for automation
    if not result.wasSuccessful():
        sys.exit(1)

if __name__ == '__main__':
    run_all_tests()