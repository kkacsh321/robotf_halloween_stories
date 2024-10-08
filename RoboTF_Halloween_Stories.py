import streamlit as st
from langchain_openai import ChatOpenAI
from requests.exceptions import RequestException
import requests

# Function to generate story stream
def generate_story_stream(api_key, endpoint, model, prompt):
    llm = ChatOpenAI(
        base_url=endpoint,
        openai_api_key=api_key,
        model_name=model,
        streaming=True
    )

    formatted_input = [{"role": "user", "content": prompt}]

    return llm.stream(formatted_input)

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
    api_key = st.sidebar.text_input("OpenAI API Key (Leave Blank for LocalAI)", type="password", value="1234")
    default_endpoint = st.sidebar.selectbox("Default Endpoint", ["https://api.openai.com/v1", "http://localai:8080/v1"], index=1)

    st.sidebar.write("Or Use Another API")

    custom_endpoint = st.sidebar.text_input("Custom Endpoint (optional)", "")

    endpoint = custom_endpoint if custom_endpoint else default_endpoint

    # Get the list of available models
    models = get_llm_models(endpoint, api_key)

    # Sidebar to select the LLM model
    model = st.sidebar.selectbox("Select LLM Model", models)

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
            # Generate and stream the story into the placeholder
            story_placeholder.write_stream(generate_story_stream(api_key, endpoint, model, prompt))

if __name__ == "__main__":
    main()
