import emoji
import io
import re
import requests
import streamlit as st
from langchain_openai import ChatOpenAI
from requests.exceptions import RequestException

accumulated_story = ""

# Function to generate story stream
def generate_story_stream(api_key, endpoint, model, prompt, on_complete_callback=None):
    llm = ChatOpenAI(
        base_url=endpoint,
        openai_api_key=api_key,
        model_name=model,
        streaming=True
    )

    formatted_input = [{"role": "user", "content": prompt}]
    if on_complete_callback:
        on_complete_callback(accumulated_story)
    return llm.stream(formatted_input)

# Function to handle the completion of the story generation
def on_story_complete(story):
    # This function will be called once the story streaming is complete
    # You can now use the accumulated_story variable as needed
    global accumulated_story
    accumulated_story = story
    print("Story complete:", accumulated_story)

# Function to remove emojis and special characters for better TTS
def remove_emojis(text):
    # Remove emoji using the emoji library
    text_without_emojis = emoji.replace_emoji(text, replace='')

    # Remove asterisks using regex
    text_without_asterisks = re.sub(r"\*", '', text_without_emojis)

    # Remove quotes (single and double)
    text_without_quotes = re.sub(r"[\"']", '', text_without_asterisks)

    # Remove line breaks and extra spaces
    text_without_linebreaks = text_without_quotes.replace("\n", " ").replace("\r", " ").strip()

    # Remove special characters (except for alphanumeric and spaces)
    clean_text = re.sub(r"[^a-zA-Z0-9\s]", '', text_without_linebreaks)

    # Replace multiple spaces with a single space
    final_cleaned_text = re.sub(r"\s+", ' ', clean_text)

    return final_cleaned_text

# Function to get the TTS wav file
def text_to_speech(text, endpoint, api_key, tts_model, voice_selection):
    """
    Convert text to speech using the provided TTS endpoint and model.
    """

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    if 'api.openai.com' in endpoint:
        # If it does, append '/audio/speech' to the endpoint
        tts_endpoint = endpoint + '/audio/speech'
        payload = {
            "input": text,
            "model": tts_model,
            "voice": voice_selection,
            "response_format": "wav"
        }
    else:
        # If it does not, replace '/v1' with '/tts' for LocalAI
        tts_endpoint = endpoint.replace("/v1", "/tts")
        payload = {
            "model": voice_selection+".onnx",
            "backend": "piper",
            "input": text
        }

    print(f"tts_endpoint: {tts_endpoint}")
    print(f"tts_model: {tts_model}")
    print(f"voice: {voice_selection}")
    print(f"Payload: {payload}")

    response = requests.post(tts_endpoint, headers=headers, json=payload)
    print(f"request: {response}")
    if response.status_code == 200:
        audio_content = response.content
        print(response)
        print(response.status_code)

        audio_content = response.content

        with open('temp_audio.wav', 'wb') as f:
            f.write(audio_content)

        return io.BytesIO(audio_content)

    else:
        raise RequestException(f"TTS request failed with status code {response.status_code}")

# Function to play the audio
def play_audio(audio_bytes):
    """
    Play audio directly within the Streamlit app.
    """
    st.audio(audio_bytes, format='audio/wav', autoplay=True)

# Function to query models from LLM URL
def get_llm_models(llm_url, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(f"{llm_url}/models", headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        if response.status_code == 200:
            return [model['id'] for model in response.json().get('data', [])]
        else:
            st.error("Failed to fetch models. Status code: {response.status_code}")
            return []

    except RequestException as e:
        st.error(f"Request failed (Please set your API Key or Check to make sure LocalAI/other is running): {e}")
        return []

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return []

def main():
    # Streamlit app
    st.title("RoboTF Halloween Story Generator")

    st.image("images/robotf_halloween.jpg")
    st.sidebar.title("Settings")
    api_key = st.sidebar.text_input("OpenAI API Key (Leave Blank for LocalAI unless API Key set on Server)", type="password", value="1234")
    default_endpoint = st.sidebar.selectbox("Default Endpoint", ["https://api.openai.com/v1", "http://localai:8080/v1", "http://localhost:8080/v1"], index=1)

    st.sidebar.write("Or Use Another API")

    custom_endpoint = st.sidebar.text_input("Custom Endpoint (optional)", "")

    endpoint = custom_endpoint if custom_endpoint else default_endpoint

    # Get the list of available models
    models = get_llm_models(endpoint, api_key)

    # Sidebar to select the LLM model
    model = st.sidebar.selectbox("Select LLM Model", models)

    tts_model = st.sidebar.selectbox("Select the TTS Model", models)

        # Check if the endpoint contains 'api.openai.com'
    if 'api.openai.com' in endpoint:
        # If it does, append '/audio/speech' to the endpoint
        voice_list = [
            "alloy",
            "echo",
            "fable",
            "onyx",
            "nova",
            "shimmer"
            ]
    else:
        # If it does not, replace '/v1' with '/tts'
        voice_list = [
            "en-us-amy-low",
            "en-gb-alan-low",
            "en-gb-southern_english_female-low",
            "en-us-danny-low",
            "en-us-kathleen-low",
            "en-us-lessac-low",
            "en-us-lessac-medium",
            "en-us-libritts-high",
            "en-us-ryan-high",
            "en-us-ryan-low",
            "en-us-ryan-medium",
        ]

    voice_selection = st.sidebar.selectbox("Select the Voice", voice_list)

    # Show default prompt and allow changes
    st.write(':green[User Prompt]')
    user_prompt = """Create a spooky Halloween tale where cutting-edge AI and powerful
hardware like GPUs and CPUs come to life. In this story, large language models (LLMs)
play a central role, but something goes wrong during testing, inference, power
consumption or anything else that is AI related. Perhaps the models start
predicting strange, eerie outcomes, or the hardware begins to malfunction in ways no
one expected. The tale should blend technological horror with classic Halloween
spookiness, maybe some humor focusing on how human and machine interact in a world
where the boundary between them is blurring. It must include pizza as an element.
Otherwise use the following an example elements or create your own in the story:
- A mysterious lab where LLMs are trained and tested late at night.
- Unexplainable glitches during inference that seem almost supernatural.
- GPU and CPU hardware behaving erratically, like heating up mysteriously or making
    odd noises.
- The concept of testing AI models that seem to take on a life of their own, predicting
    strange and frightening scenarios.
Your goal is to create a chilling narrative that makes the world of AI and hardware
testing feel ominous, as if the technology itself has become haunted.
You can include the use of emojis in your story.

ALWAYS end with saying "RoboTF wishes you a Happy Halloween! 👻
"""
    prompt = st.text_area(':green[Prompt to use:]', user_prompt, key="user_prompt", height=400)

    # Create a placeholder for the story
    story_placeholder = st.empty()

    if st.button("Generate RoboTF Halloween Story"):
        print("Generate Story Button Clicked")
        if api_key and endpoint and model:
            # Clear the story placeholder before generating a new story
            story_placeholder.empty()
            # Update the global accumulated_story variable
            global accumulated_story
            # Generate and stream the story into the placeholder
            # Pass the on_story_complete function as a callback
            accumulated_story = story_placeholder.write_stream(generate_story_stream(api_key, endpoint, model, prompt, on_complete_callback=on_story_complete))
            # The on_story_complete function will be called with the full story content
            print(accumulated_story)
            st.session_state['accumulated_story'] = accumulated_story


    if st.button("Speak It To Me"):
        print("Speak it to Me Button Clicked")
        # Retrieve the generated story
        print(f"Full Story: {st.session_state['accumulated_story']}")
        story_text = st.session_state['accumulated_story']
        clean_text = remove_emojis(story_text)
        print(f"Clean Text: {clean_text}")
        st.text_area(':green[Generated Story:]', story_text, key="story_text", height=400)
        # Convert the story to speech
        audio_bytes = text_to_speech(clean_text, endpoint, api_key, tts_model, voice_selection)
        # Play the audio
        play_audio(audio_bytes)

if __name__ == "__main__":
    main()
