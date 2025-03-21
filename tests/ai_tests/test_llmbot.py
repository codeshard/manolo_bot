import unittest
import unittest.mock

from langchain_core.messages import AIMessage, HumanMessage
from requests import RequestException

from ai.llmbot import LLMBot
from config import Config


class TestLlmBot(unittest.TestCase):
    def get_basic_llm_bot(self):
        mock_config = unittest.mock.MagicMock(spec=Config)
        mock_config.ollama_model = "test_model"
        mock_config.google_api_key = None
        mock_config.openai_api_key = None
        mock_config.openai_api_base_url = None
        system_instructions = "You are a helpful assistant"
        messages_buffer = []
        return LLMBot(mock_config, system_instructions, messages_buffer)  # Initialize the bot

    def test_llm_bot__init_with_ollama_ai(self):
        # Arrange
        mock_config = unittest.mock.MagicMock(spec=Config)
        mock_config.ollama_model = "ollama_model"
        mock_config.google_api_key = None
        mock_config.google_api_model = None
        mock_config.openai_api_key = None
        mock_config.openai_api_base_url = None

        with (
            unittest.mock.patch("ai.llmbot.ChatGoogleGenerativeAI") as mock_chat_google,
            unittest.mock.patch("ai.llmbot.ChatOllama") as mock_chat_ollama,
            unittest.mock.patch("ai.llmbot.ChatOpenAI") as mock_chat_openai,
        ):
            system_instructions = "You are a helpful assistant"
            messages_buffer = []

            # Act
            bot = LLMBot(mock_config, system_instructions, messages_buffer)

            # Assert
            mock_chat_ollama.assert_called_once()
            mock_chat_google.assert_not_called()
            mock_chat_openai.assert_not_called()
            self.assertEqual(bot.system_instructions, system_instructions)
            self.assertEqual(bot.messages_buffer, messages_buffer)
            self.assertEqual(bot.config, mock_config)
            self.assertIsNotNone(bot.llm)

    def test_llm_bot__init_with_google_ai(self):
        # Arrange
        mock_config = unittest.mock.MagicMock(spec=Config)
        mock_config.ollama_model = None
        mock_config.google_api_key = "fake_google_key"
        mock_config.google_api_model = "gemini-2.0-flash"
        mock_config.openai_api_key = None
        mock_config.openai_api_base_url = None

        with (
            unittest.mock.patch("ai.llmbot.ChatGoogleGenerativeAI") as mock_chat_google,
            unittest.mock.patch("ai.llmbot.ChatOllama") as mock_chat_ollama,
            unittest.mock.patch("ai.llmbot.ChatOpenAI") as mock_chat_openai,
        ):
            system_instructions = "You are a helpful assistant"
            messages_buffer = []

            # Act
            bot = LLMBot(mock_config, system_instructions, messages_buffer)

            # Assert
            mock_chat_google.assert_called_once()
            mock_chat_ollama.assert_not_called()
            mock_chat_openai.assert_not_called()
            self.assertEqual(bot.system_instructions, system_instructions)
            self.assertEqual(bot.messages_buffer, messages_buffer)
            self.assertEqual(bot.config, mock_config)
            self.assertIsNotNone(bot.llm)

    def test_llm_bot__init_with_openai_ai(self):
        # Arrange
        mock_config = unittest.mock.MagicMock(spec=Config)
        mock_config.ollama_model = None
        mock_config.google_api_key = None
        mock_config.google_api_model = None
        mock_config.openai_api_key = "fake_openai_key"
        mock_config.openai_api_base_url = None

        with (
            unittest.mock.patch("ai.llmbot.ChatGoogleGenerativeAI") as mock_chat_google,
            unittest.mock.patch("ai.llmbot.ChatOllama") as mock_chat_ollama,
            unittest.mock.patch("ai.llmbot.ChatOpenAI") as mock_chat_openai,
        ):
            system_instructions = "You are a helpful assistant"
            messages_buffer = []

            # Act
            bot = LLMBot(mock_config, system_instructions, messages_buffer)

            # Assert
            mock_chat_google.assert_not_called()
            mock_chat_ollama.assert_not_called()
            mock_chat_openai.assert_called_once()
            self.assertEqual(bot.system_instructions, system_instructions)
            self.assertEqual(bot.messages_buffer, messages_buffer)
            self.assertEqual(bot.config, mock_config)
            self.assertIsNotNone(bot.llm)

    def test_llm_bot__init_raises_exception_with_no_llm_backend(self):
        # Arrange
        mock_config = unittest.mock.MagicMock(spec=Config)
        mock_config.ollama_model = None
        mock_config.google_api_key = None
        mock_config.openai_api_key = None
        mock_config.openai_api_base_url = None

        system_instructions = "You are a helpful assistant"
        messages_buffer = []

        # Act & Assert
        with self.assertRaises(Exception) as context:
            LLMBot(mock_config, system_instructions, messages_buffer)

        self.assertEqual(str(context.exception), "No LLM backend data found")

    def test_extract_url__extract_valid_url(self):
        # Arrange
        bot = self.get_basic_llm_bot()
        text = "Check out this website: https://example.com/page?param=value"

        # Act
        result = bot._extract_url(text)

        # Assert
        self.assertEqual(result, "https://example.com/page?param=value")

    def test_extract_url__return_none_when_no_url(self):
        # Arrange
        bot = self.get_basic_llm_bot()
        text = "This is a text without any URL in it"

        # Act
        result = bot._extract_url(text)

        # Assert
        self.assertIsNone(result)

    def test_remove_url__removes_http_urls_from_text(self):
        # Arrange
        bot = self.get_basic_llm_bot()
        text_with_urls = "Check this link https://example.com and this one http://test.org/page?param=1"

        # Act
        result = bot._remove_urls(text_with_urls)

        # Assert
        self.assertEqual("Check this link  and this one ", result)

    def test_remove_url__handles_empty_string_input(self):
        # Arrange
        bot = self.get_basic_llm_bot()
        empty_text = ""

        # Act
        result = bot._remove_urls(empty_text)

        # Assert
        self.assertEqual("", result)

    def test_call_sdapi__successful_api_call(self):
        # Arrange
        config_mock = unittest.mock.MagicMock()
        config_mock.sdapi_url = "http://test-sd-api.com"
        config_mock.sdapi_params = {
            "steps": 1,
            "cfg_scale": 1,
            "width": 512,
            "height": 512,
            "timestep_spacing": "trailing",
        }
        config_mock.sdapi_negative_prompt = None

        llm_bot = self.get_basic_llm_bot()
        llm_bot.config = config_mock

        prompt = "a beautiful landscape"
        expected_response = {"images": ["base64_image_data"]}

        mock_response = unittest.mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response

        with unittest.mock.patch("requests.post", return_value=mock_response) as mock_post:
            # Act
            result = llm_bot.call_sdapi(prompt)

            # Assert
            mock_post.assert_called_once_with(
                "http://test-sd-api.com/sdapi/v1/txt2img", json={**config_mock.sdapi_params, "prompt": prompt}
            )
            self.assertEqual(result, expected_response)

    def test_call_sdapi__non_200_response(self):
        # Arrange
        config_mock = unittest.mock.MagicMock()
        config_mock.sdapi_url = "http://test-sd-api.com"
        config_mock.sdapi_params = {
            "steps": 1,
            "cfg_scale": 1,
            "width": 512,
            "height": 512,
            "timestep_spacing": "trailing",
        }

        llm_bot = self.get_basic_llm_bot()
        llm_bot.config = config_mock

        prompt = "a beautiful landscape"

        mock_response = unittest.mock.MagicMock()
        mock_response.status_code = 404

        with unittest.mock.patch("requests.post", return_value=mock_response) as mock_response:
            # Act
            result = llm_bot.call_sdapi(prompt)

            # Assert
            self.assertIsNone(result)

    def test_answer_image_message__successful_image_message_processing(self):
        # Arrange
        llm_bot = self.get_basic_llm_bot()
        text = "What's in this image?"
        image_url = "https://example.com/image.jpg"
        messages = []

        # Mock requests.get
        mock_response = unittest.mock.Mock()
        mock_response.content = b"fake_image_data"
        with unittest.mock.patch("requests.get", return_value=mock_response):
            # Mock LLM response
            expected_response = AIMessage(content="This is an image of a cat")
            llm_bot.llm = unittest.mock.Mock()
            llm_bot.llm.invoke.return_value = expected_response

            # Act
            response = llm_bot.answer_image_message(text, image_url, messages)

            # Assert
            self.assertEqual(response, expected_response)
            self.assertEqual(len(messages), 1)
            llm_bot.llm.invoke.assert_called_once_with(messages)

    def test_answer_image_message__handles_request_exception(self):
        # Arrange
        llm_bot = self.get_basic_llm_bot()
        text = "What's in this image?"
        image_url = "https://invalid-url.com/image.jpg"
        messages = []

        # Mock requests.get to raise RequestException
        # unittest.mock.patch("requests.get", side_effect=RequestException("Failed to get image"))
        with (
            unittest.mock.patch("requests.get", side_effect=RequestException("Failed to get image")),
            unittest.mock.patch("logging.error") as mock_logger,
            unittest.mock.patch("logging.exception") as mock_exception_logger,
        ):
            # Act
            response = llm_bot.answer_image_message(text, image_url, messages)

            # Assert
            self.assertEqual(response.content, "NO_ANSWER")
            self.assertEqual(response.type, "text")
            mock_logger.assert_called_once_with(f"Failed to get image: {image_url}")
            mock_exception_logger.assert_called_once()
            self.assertEqual(len(messages), 0)  # No message should be added to the list

    def test_generate_image__success(self):
        # Arrange
        llm_bot = self.get_basic_llm_bot()
        mock_response = {"images": ["base64_encoded_image_data"]}
        with unittest.mock.patch.object(llm_bot, "call_sdapi", return_value=mock_response) as mock_call_sdapi:
            # Act
            result = llm_bot.generate_image("a beautiful landscape")

            # Assert
            self.assertEqual(result, "base64_encoded_image_data")
            mock_call_sdapi.assert_called_once_with("a beautiful landscape")

    def test_generate_image__returns_none(self):
        # Arrange
        llm_bot = self.get_basic_llm_bot()
        with unittest.mock.patch.object(llm_bot, "call_sdapi", return_value=None) as mock_call_sdapi:
            # Act
            result = llm_bot.generate_image("a beautiful landscape")

            # Assert
            self.assertIsNone(result)
            mock_call_sdapi.assert_called_once_with("a beautiful landscape")

    def test_count_tokens__with_string_content(self):
        # Arrange
        llm_bot = self.get_basic_llm_bot()
        messages = [HumanMessage(content="Hello"), HumanMessage(content="World")]
        mock_llm_chain = unittest.mock.MagicMock()
        mock_llm_chain.get_num_tokens.return_value = 2

        # Act
        result = llm_bot.count_tokens(messages, mock_llm_chain)

        # Assert
        self.assertEqual(result, 2)
        mock_llm_chain.get_num_tokens.assert_called_once_with("Hello World")

    def test_count_tokens__with_list_content(self):
        # Arrange
        llm_bot = self.get_basic_llm_bot()
        messages = [HumanMessage(content="Hello"), AIMessage(content=["World", "Test"])]
        mock_llm_chain = unittest.mock.MagicMock()
        mock_llm_chain.get_num_tokens.return_value = 3

        # Act
        result = llm_bot.count_tokens(messages, mock_llm_chain)

        # Assert
        self.assertEqual(result, 3)
        mock_llm_chain.get_num_tokens.assert_called_once_with("Hello ['World', 'Test']")

    # TODO: find a way to test this method as it is raising a pydantic validation error
    # def test_answer_webcontent__successful_url_extraction_and_processing(self):
    #     # Arrange
    #     llm_bot = self.get_basic_llm_bot()
    #     llm_bot.llm = unittest.mock.Mock()
    #
    #     message_text = "Summarize this webpage"
    #     response_content = "Check out this link: https://example.com/page"
    #     url = "https://example.com/page"
    #
    #     # Mock _extract_url to return our test URL
    #     # unittest.mock.patch.object(llm_bot, '_extract_url', return_value=url)
    #
    #     # Mock WebBaseLoader
    #     mock_loader = unittest.mock.Mock()
    #     mock_docs = [unittest.mock.Mock()]
    #     mock_loader.load.return_value = mock_docs
    #
    #     # Mock StuffDocumentsChain
    #     mock_chain = unittest.mock.Mock()
    #     mock_chain.invoke.return_value = {"output_text": "This is a summary of the webpage."}
    #
    #     with (
    #         unittest.mock.patch.object(llm_bot, "_extract_url", return_value=url) as _extract_url_mock,
    #         unittest.mock.patch.object(
    #             llm_bot, "_remove_urls", return_value="Summarize this webpage"
    #         ) as _remove_urls_mock,
    #         unittest.mock.patch("langchain_community.document_loaders.WebBaseLoader", return_value=mock_loader),
    #         unittest.mock.patch(
    #             "langchain.chains.combine_documents.stuff.StuffDocumentsChain", return_value=mock_chain
    #         ),
    #     ):
    #         # Act
    #         result = llm_bot.answer_webcontent(message_text, response_content)
    #
    #         # Assert
    #         self.assertEqual(result, "This is a summary of the webpage.")
    #         _extract_url_mock.assert_called_once_with(response_content)
    #         _remove_urls_mock.assert_called_once_with(message_text)
    #         mock_loader.load.assert_called_once()
    #         mock_chain.invoke.assert_called_once_with(mock_docs)

    def test_answer_webcontent__no_url_found_returns_none(self):
        # Arrange
        llm_bot = self.get_basic_llm_bot()

        message_text = "Summarize this webpage"
        response_content = "There is no URL in this content"

        # Mock _extract_url to return None (no URL found)
        unittest.mock.patch.object(llm_bot, "_extract_url", return_value=None)
        with (
            unittest.mock.patch.object(llm_bot, "_extract_url", return_value=None) as _extract_url_mock,
            unittest.mock.patch.object(llm_bot, "_remove_urls") as _remove_urls_mock,
        ):
            # Act
            result = llm_bot.answer_webcontent(message_text, response_content)

            # Assert
            self.assertIsNone(result)
            _extract_url_mock.assert_called_once_with(response_content)
            # Verify that _remove_urls was not called since no URL was found
            _remove_urls_mock.assert_not_called()

    # TODO: find a way to test process_message_buffer logic, probably the function needs a refactor to make it more
    #  testable


if __name__ == "__main__":
    unittest.main()
