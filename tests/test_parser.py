import unittest

from mcdreforged.api.rtext import RText, RAction, RColor

from gugubot.parser.message.array import ArrayHandler
from gugubot.parser.message.messageBuilder import MessageBuilder
from gugubot.parser.message.mcMessageBuilder import mcMessageBuilder
from gugubot.parser.message.CQ import CQHandler

class TestParserMessageArray(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        print("\n** Testing Parser Message Array **")

    def test_parser(self):
        handler = ArrayHandler()

        test_dict = [
            {'type': 'text', 'data': {'text': 'Hello '}},
            {'type': 'face', 'data': {'id': '1'}},
            {'type': 'text', 'data': {'text': ' World '}},
            {'type': 'at', 'data': {'qq': '12345'}},
            {'type': 'text', 'data': {'text': '!'}},
        ]

        self.assertEqual(handler.parse(test_dict), test_dict)

    def test_build(self):
        handler = ArrayHandler()

        test_dict = [
            {'type': 'text', 'data': {'text': 'Hello '}},
            {'type': 'face', 'data': {'id': '1'}},
            {'type': 'text', 'data': {'text': ' World '}},
            {'type': 'at', 'data': {'qq': '12345'}},
            {'type': 'text', 'data': {'text': '!'}},
        ]

        self.assertEqual(handler.build(test_dict), test_dict)

class TestParserMessageCQ(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        print("\n** Testing Parser Message CQ **")

    def test_parser(self):
        handler = CQHandler()

        test_str_1 = "Hello [CQ:face,id=1] World [CQ:at,qq=12345]!"
        test_ans_1 = [
            {'type': 'text', 'data': {'text': 'Hello '}},
            {'type': 'face', 'data': {'id': '1'}},
            {'type': 'text', 'data': {'text': ' World '}},
            {'type': 'at', 'data': {'qq': '12345'}},
            {'type': 'text', 'data': {'text': '!'}},
        ]

        self.assertEqual(handler.parse(test_str_1), test_ans_1)
        self.assertEqual(handler.build(test_ans_1), test_str_1)

    def test_build(self):
        handler = CQHandler()

        test_ans = "Hello [CQ:face,id=1] World [CQ:at,qq=12345]!"
        test_dict = [
            {'type': 'text', 'data': {'text': 'Hello '}},
            {'type': 'face', 'data': {'id': '1'}},
            {'type': 'text', 'data': {'text': ' World '}},
            {'type': 'at', 'data': {'qq': '12345'}},
            {'type': 'text', 'data': {'text': '!'}},
        ]

        self.assertEqual(handler.build(test_dict), test_ans)

class TestParserMessageMcBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        print("\n** Testing Parser Message McMessageBuilder **")

    def test_build(self):
        mcmb = mcMessageBuilder()

        forward_content = "Text Message"
        ans = RText(f"[QQ] ", color=RColor.gold) + RText(forward_content, color=RColor.white)

        self.assertEqual(str(mcmb.build(forward_content)), str(ans))

class TestParserMessageMessageBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        print("\n** Testing Parser Message MessageBuilder **")

    def test_text(self):
        mb = MessageBuilder()

        test_str = "Hello World!"
        test_ans = {'type': 'text', 'data': {'text': "Hello World!"}}

        self.assertEqual(mb.text(test_str), test_ans)

    def test_at(self):
        mb = MessageBuilder()

        test_str = 123456
        test_ans = {'type': 'at', 'data': {'qq': "123456"}}

        self.assertEqual(mb.at(test_str), test_ans)

    def test_image(self):
        mb = MessageBuilder()

        test_str = 'abcd.png'
        test_ans = {'type': 'image', 'data': {'file': "abcd.png"}}

        self.assertEqual(mb.image(test_str), test_ans)

    def test_voice(self):
        mb = MessageBuilder()

        test_str = 'abcd.wav'
        test_ans = {'type': 'record', 'data': {'file': 'abcd.wav'}}

        self.assertEqual(mb.voice(test_str), test_ans)

    def test_face(self):
        mb = MessageBuilder()

        test_str = 1
        test_ans = {'type': 'face', 'data': {'id': "1"}}

        self.assertEqual(mb.face(test_str), test_ans)

    def test_bface(self):
        mb = MessageBuilder()

        test_str = 1
        test_ans = {'type': 'bface', 'data': {'id': "1"}}

        self.assertEqual(mb.bface(test_str), test_ans)

    def test_sface(self):
        mb = MessageBuilder()

        test_str = 1
        test_ans = {'type': 'sface', 'data': {'id': "1"}}

        self.assertEqual(mb.sface(test_str), test_ans)

    def test_location(self):
        mb = MessageBuilder()

        lat = 108
        lon = 30
        title = "Test Location"
        content = "This is a test location."
        test_ans = {'type': 'location', 'data': {'lat': "108", 'lon': "30", 'title': title, 'content': content}}

        self.assertEqual(mb.location(lat, lon, title, content), test_ans)

    def test_share(self):
        mb = MessageBuilder()

        url = "https://example.com"
        title = "Example Title"
        content = "This is an example content."
        image = "https://example.com/image.png"
        test_ans = {
            "type": "share",
            "data": {
                "url": url,
                "title": title,
                "content": content,
                "image": image,
            },
        }

        self.assertEqual(mb.share(url, title, content, image), test_ans)

    def test_contact(self):
        mb = MessageBuilder()

        type_ = "group"
        id = 123456
        test_ans = {'type': 'contact', 'data': {'type': "group", 'id':"123456"}}

        self.assertEqual(mb.contact(type_, id), test_ans)

    def test_reply(self):
        mb = MessageBuilder()

        test_str = 1
        test_ans = {'type': 'reply', 'data': {'id': "1"}}

        self.assertEqual(mb.reply(test_str), test_ans)

    def test_poke(self):
        mb = MessageBuilder()

        test_str = 123456
        test_ans = {'type': 'poke', 'data': {'qq': "123456"}}

        self.assertEqual(mb.poke(test_str), test_ans)

    def test_dice(self):
        mb = MessageBuilder()

        test_ans = {'type': 'dice', 'data': {}}

        self.assertEqual(mb.dice(), test_ans)

    def test_rps(self):
        mb = MessageBuilder()

        test_ans = {'type': 'rps', 'data': {}}

        self.assertEqual(mb.rps(), test_ans)

    def test_shake(self):
        mb = MessageBuilder()

        test_ans = {'type': 'shake', 'data': {}}

        self.assertEqual(mb.shake(), test_ans)
