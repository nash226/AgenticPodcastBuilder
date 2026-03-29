import gradio as gr

from chatbot import generate_podcast


def build_podcast(topic, duration_minutes):
    if not topic or not topic.strip():
        raise gr.Error("Enter a topic before generating a podcast.")

    status = (
        f"Generating a podcast about '{topic.strip()}' for approximately "
        f"{duration_minutes} minutes."
    )
    summary, audio_path = generate_podcast(topic.strip(), int(duration_minutes))
    return status, summary, audio_path


with gr.Blocks(title="Agentic Podcast Builder") as demo:
    gr.Markdown(
        """
        # Agentic Podcast Builder
        Generate a researched podcast episode and download the resulting MP3.
        """
    )

    with gr.Row():
        topic = gr.Textbox(
            label="Podcast Topic",
            placeholder="Example: How AI voice agents are changing media",
        )
        duration_minutes = gr.Slider(
            minimum=1,
            maximum=20,
            value=5,
            step=1,
            label="Duration (minutes)",
        )

    generate_button = gr.Button("Generate Podcast", variant="primary")
    status = gr.Textbox(label="Status", interactive=False)
    summary = gr.Textbox(label="Assistant Summary", lines=10, interactive=False)
    audio_file = gr.File(label="Download MP3")

    generate_button.click(
        fn=build_podcast,
        inputs=[topic, duration_minutes],
        outputs=[status, summary, audio_file],
    )


if __name__ == "__main__":
    demo.launch(share=True)
