import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider
from chainlit.types import ThreadDict
import auth  # Import the auth module to ensure the oauth_callback is registered
import llm
import asyncio
from search import perform_semantic_search  
import tiktoken

# Define method A to handle messages with attachments
# https://github.com/Chainlit/cookbook/tree/main/audio-assistant
async def handle_attachments(msg: cl.Message):
    # Processing images exclusively
    images = [file for file in msg.elements if "image" in file.mime]

    if not images:
        await cl.Message(content="No image files attached").send()
        return

    # Read the first image
    with open(images[0].path, "rb") as f:
        pass  # Add your image processing logic here

    await cl.Message(content=f"Received {len(images)} image(s)").send()

# # Define method B to handle messages without attachments
# async def handle_no_attachments(msg: cl.Message):
#     response = llm.chat(msg.content)

#     # Simulate typing by sending multiple characters at a time
#     message = await cl.Message(content="").send()  # Initialize an empty message
#     chunk_size = 100  # Number of characters per chunk
#     typing_delay = 0.0001  # Delay between each chunk, adjust as needed

#     for i in range(0, len(response), chunk_size):
#         chunk = response[i:i + chunk_size]
#         message.content += chunk
#         await message.update()  # Update the message with the new content
#         await asyncio.sleep(typing_delay)  # Delay to simulate typing

#     # await cl.Message(content=response).send()

# def chunk_text(text, max_tokens):
#     enc = tiktoken.encoding_for_model("gpt-4o")
#     tokens = enc.encode(text)
#     chunks = []
#     for i in range(0, len(tokens), max_tokens):
#         chunk = enc.decode(tokens[i:i+max_tokens])
#         chunks.append(chunk)
#     return chunks
    
async def handle_no_attachments(msg):
    # # Define the maximum allowed tokens for the input (based on Microsoft OpenAI's limit)
    # MAX_TOKENS = 128000  # 128,000 tokens limit

    # # Initialize the tokenizer with the correct encoding
    # tokenizer = tiktoken.get_encoding("cl100k_base")  # Use "cl100k_base" for GPT-3.5-turbo and GPT-4

    # Ensure the search is triggered only once per message
    if not msg.content:
        return  # If there's no content, skip

    # Use the original user query
    user_query = msg.content

    # Check if the query is a simple greeting
    simple_greetings = ["hello", "hi", "hey"]
    if any(greeting.lower() in user_query.lower() for greeting in simple_greetings):
        response = llm.chat(user_query)
    else:
        # Perform the search once
        print("Search called")
        search_results = perform_semantic_search(user_query)
        print("Search completed")

        
        # Combine the user query with the search results
        ai_prompt_template = "Please provide a response strictly based on the context and information provided. Do not include any external information or assumptions. The query is: '{}'. Focus only on the details within this context: '{}'. Make sure to return all the urls in [Reference: ] section."

        combined_input = ai_prompt_template.format(user_query, search_results)

        response = llm.chat(combined_input)
        # # Tokenize the combined input
        # tokens = tokenizer.encode(combined_input)

        # # Check if the token count exceeds the maximum allowed tokens
        # if len(tokens) > MAX_TOKENS:
        #     # Split the tokens into chunks of maximum allowed tokens
        #     chunks = [tokens[i:i + MAX_TOKENS] for i in range(0, len(tokens), MAX_TOKENS)]
        #     responses = []
            
        #     for chunk in chunks:
        #         # Decode the chunk back to text before sending it to the LLM
        #         chunk_text = tokenizer.decode(chunk)
        #         response_chunk = llm.chat(chunk_text)  # Send each chunk separately
        #         responses.append(response_chunk)
            
        #     # Combine all responses into one final response
        #     response = ''.join(responses)
        # else:
        #     # If the token count is within the allowed limit, send it directly
        #     response = llm.chat(combined_input)

    # Simulate typing and send the response
    message = await cl.Message(content="").send()  # Initialize an empty message
    chunk_size = 100  # Number of characters per chunk
    typing_delay = 0.0001  # Delay between each chunk, adjust as needed

    for i in range(0, len(response), chunk_size):
        chunk = response[i:i + chunk_size]
        message.content += chunk
        await message.update()  # Update the message with the new content
        await asyncio.sleep(typing_delay)  # Delay to simulate typing
# @cl.set_chat_profiles
# async def chat_profile():
#     return [       
#         cl.ChatProfile(
#             name="GPT-4o",
#             markdown_description="The underlying LLM model is **GPT-4o**.",
#             icon="/public/avatars/my_assistant.png",
#         ),
#          cl.ChatProfile(
#             name="gpt-3.5-turbo",
#             markdown_description="The underlying LLM model is **GPT-3.5-turbo**.",
#             icon="/public/avatars/my_assistant2.png",
#         ),
#     ]

# On setting update
@cl.on_settings_update
async def setup_agent(settings):
    print("on_settings_update", settings)

# On chat start
@cl.on_chat_start
async def on_chat_start():
    chat_profile = cl.user_session.get("chat_profile")
    await cl.Message(
        content=f"starting chat using the {chat_profile} chat profile"
    ).send()

# On message
@cl.on_message
async def on_message(msg: cl.Message):
    if msg.elements:
        await handle_attachments(msg)
    else:
        await handle_no_attachments(msg)

# On chat stop
@cl.on_stop
def on_stop():
    print("The user wants to stop the task!")

# On chat end
@cl.on_chat_end
def on_chat_end():
    print("The user disconnected!")

# On chat resume
@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    print("The user resumed a previous chat session!")

@cl.on_chat_start
async def start():
    settings = await cl.ChatSettings(
        [
            # Select(
            #     id="Model",
            #     label="OpenAI - Model",
            #     values=["GPT-4o", "GPT-3.5-turbo"],
            #     initial_index=0,
            # ),
            # Switch(id="Streaming", label="OpenAI - Stream Tokens", initial=True),
            Slider(
                id="Temperature",
                label="Temperature",
                initial=0,
                min=0,
                max=2,
                step=0.1,
            ),
            # Slider(
            #     id="SAI_Steps",
            #     label="Stability AI - Steps",
            #     initial=30,
            #     min=10,
            #     max=150,
            #     step=1,
            #     description="Amount of inference steps performed on image generation.",
            # ),
            # Slider(
            #     id="SAI_Cfg_Scale",
            #     label="Stability AI - Cfg_Scale",
            #     initial=7,
            #     min=1,
            #     max=35,
            #     step=0.1,
            #     description="Influences how strongly your generation is guided to match your prompt.",
            # ),
            # Slider(
            #     id="SAI_Width",
            #     label="Stability AI - Image Width",
            #     initial=512,
            #     min=256,
            #     max=2048,
            #     step=64,
            #     tooltip="Measured in pixels",
            # ),
            # Slider(
            #     id="SAI_Height",
            #     label="Stability AI - Image Height",
            #     initial=512,
            #     min=256,
            #     max=2048,
            #     step=64,
            #     tooltip="Measured in pixels",
            # ),
        ]
    ).send()

# Run the application
if __name__ == "__main__":
    cl.run()