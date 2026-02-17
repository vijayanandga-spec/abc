
import unittest
import os
from apminsight.agentfactory import get_agent

class AgentFactoryTest(unittest.TestCase):

    def test_get_agent(self):
        self.assertTrue(get_agent() is not None)

    
        