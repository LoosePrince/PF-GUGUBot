import unittest

from gugubot.config.BasicConfig import BasicConfig
from gugubot.config.BotConfig import BotConfig

class TestBasicConfig(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        print("\n** Testing Config BasicConfig **")

    def test_init_default(self):
        # Test initialization with default parameters
        config = BasicConfig()
        self.assertEqual(config.path.name, "default.json")
        self.assertEqual(config.yaml_format, False)
        self.assertEqual(config.default_content, {})
        self.assertEqual(config, {})

        self.assertTrue(config.path.is_file())
        self.assertEqual(config.path.read_text(encoding='UTF-8'), '{}')

        config.path.unlink()

    def test_init_yaml(self):
        # Test initialization with YAML format
        config = BasicConfig(yaml_format=True)
        self.assertEqual(config.path.name, "default.yml")
        self.assertEqual(config.yaml_format, True)

        self.assertTrue(config.path.is_file())
        self.assertEqual(config.path.read_text(encoding='UTF-8'), '{}\n')

        config.path.unlink()

    def test_load(self):
        # Test loading from a file
        config = BasicConfig()
        config.path.write_text('{"key": "value"}', encoding='UTF-8')
        config.load()
        self.assertEqual(config["key"], "value")

        config.path.unlink()

    def test_auto_save(self):
        # Test auto-saving functionality
        config = BasicConfig()
        config["key"] = "value"
        self.assertEqual(config["key"], "value")
        self.assertEqual(config.path.read_text(encoding='UTF-8'), '{"key": "value"}')

        del config["key"]
        self.assertEqual(config, {})
        self.assertEqual(config.path.read_text(encoding='UTF-8'), '{}')

        config.path.unlink()

class TestBotConfig(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        print("\n** Testing Config BotConfig **")

    def test_init(self):
        # Test initialization with default parameters
        config = BotConfig(path="test_config.yml")
        self.assertEqual(config.path.name, "test_config.yml")
        self.assertEqual(config.yaml_format, True)
        self.assertEqual(config.default_content, {})
        self.assertEqual(config, {})

        self.assertTrue(config.path.is_file())
        self.assertEqual(config.path.read_text(encoding='UTF-8'), '{}\n')

        config.path.unlink()

    def test_plugin_check(self):
        # Test plugin_check method
        config = BotConfig(path="test_config.yml")
        config["admin_id"] = 12345
        config["group_id"] = 12345
        config["admin_group_id"] = None

        # Check if the plugin_check method correctly processes the config
        config.plugin_check()
        self.assertEqual(config["admin_id"], [12345])
        self.assertEqual(config["group_id"], [12345])
        self.assertEqual(config["admin_group_id"], [])

        # Test with non-list value
        config["admin_group_id"] = 12345
        config.plugin_check()
        self.assertEqual(config["admin_group_id"], [12345])

        # Test with list value
        config["admin_group_id"] = [1, 2]
        config.plugin_check()
        self.assertEqual(config["admin_group_id"], [1, 2])

        config.path.unlink()