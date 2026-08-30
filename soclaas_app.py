import os

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# Configuration
# ============================================================

load_dotenv()

API_KEY = os.environ.get("SOCLAAS_API_KEY")
BASE_URL = os.environ.get("SOCLAAS_BASE_URL")

if not API_KEY:
    raise RuntimeError("SOCLAAS_API_KEY is missing from .env")

if not BASE_URL:
    raise RuntimeError("SOCLAAS_BASE_URL is missing from .env")


# ============================================================
# SoCLaS Client
# ============================================================

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL.rstrip("/"),
    timeout=60.0,
)


# ============================================================
# Get available models
# ============================================================

def get_models():
    try:
        response = client.models.list()
        return [model.id for model in response.data]

    except Exception as e:
        print(f"Failed to get models: {e}")
        return []


models = get_models()

if not models:
    raise RuntimeError(
        "No models were returned by SoCLaS. "
        "Check your API key and BASE_URL."
    )

print("Available models:")
for model in models:
    print(f"  - {model}")


# ============================================================
# Chat function
# ============================================================
def chat(message, history, model):
    if not message.strip():
        return history

    messages = []

    # Gradio 6.x history is already in message format:
    # {"role": "user", "content": "..."}
    for msg in history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"],
        })

    # Add the new user message
    messages.append({
        "role": "user",
        "content": message,
    })

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            reasoning_effort="none",
        )

        reply = response.choices[0].message.content

        # Add assistant response
        history.append({
            "role": "user",
            "content": message,
        })

        history.append({
            "role": "assistant",
            "content": reply,
        })

        return history

    except Exception as e:
        history.append({
            "role": "user",
            "content": message,
        })

        history.append({
            "role": "assistant",
            "content": f"Error: {e}",
        })

        return history

# ============================================================
# Clear conversation
# ============================================================

def clear_chat():
    return []


# ============================================================
# GUI
# ============================================================
with gr.Blocks(title="SoCLaS Chat") as demo:

    gr.Markdown(
        """
        # SoCLaS Chat

        Chat with models available through the NUS SoCLaS API.
        """
    )

    model_dropdown = gr.Dropdown(
        choices=models,
        value=models[0],
        label="Model",
        interactive=True,
    )

    chatbot = gr.Chatbot(
        label="Conversation",
        height=600,
    )

    with gr.Row():
        message_box = gr.Textbox(
            placeholder="Type your message...",
            label="Message",
            scale=5,
            lines=2,
        )

        send_button = gr.Button(
            "Send",
            variant="primary",
            scale=1,
        )

    clear_button = gr.Button("Clear conversation")

    send_button.click(
        chat,
        inputs=[
            message_box,
            chatbot,
            model_dropdown,
        ],
        outputs=chatbot,
    ).then(
        lambda: "",
        outputs=message_box,
    )

    message_box.submit(
        chat,
        inputs=[
            message_box,
            chatbot,
            model_dropdown,
        ],
        outputs=chatbot,
    ).then(
        lambda: "",
        outputs=message_box,
    )

    clear_button.click(
        lambda: [],
        outputs=chatbot,
    )


# ============================================================
# Start server
# ============================================================

if __name__ == "__main__":
    print("\nStarting SoCLaS Chat...")
    print("Open the local URL shown below.\n")

    demo.launch()