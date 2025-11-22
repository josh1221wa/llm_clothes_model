import streamlit as st
import time
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from io import BytesIO
import PIL.Image
import zipfile

# --- session defaults ---
st.session_state.setdefault("images", [])
st.session_state.setdefault("error_status", {
    "continue_processing": True,
    "error_msg": None
})
st.session_state.setdefault("api_key", None)
st.session_state.setdefault("upload_container", None)
st.session_state.setdefault("processing", False)  # flag for processing run

def main():
    st.title("LLM Clothes Modelling")

    # show API key input at top and bind directly to session_state
    st.text_input("Enter Google AI Studio API key", type="password", key="api_key",
                  placeholder="paste your API key here (no quotes)")

    api_key = (st.session_state.get("api_key") or "").strip()
    if not api_key:
        st.warning("Please enter your Google AI Studio API key above to enable uploads.")
        return

    # API key exists — show uploader
    st.success("API key provided — you can upload images now.")
    st.session_state.upload_container = st.container()

    with st.session_state.upload_container:
        images = st.file_uploader(
            label='Upload clothing image(s)', type=['jpeg', 'jpg', 'png'],
            accept_multiple_files=True, help="Maximum 50 files (press 'Start processing' after upload)"
        )

        if images and len(images) > 50:
            st.toast("⚠️ Only 50 files can be processed at any given time!")
            return

        start_button = st.button("Start processing", type="primary")

    # Only start processing when button pressed (avoids automatic looping)
    if start_button:
        if not images or len(images) == 0:
            st.error("No files uploaded. Upload at least one image before starting.")
            return

        # cache (read) images once
        st.session_state.images = []  # reset previous images
        for i, f in enumerate(images):
            # read file bytes into BytesIO so we can reuse later
            b = BytesIO(f.read())
            st.session_state.images.append({
                "image_id": f"Image {i+1}",
                "input_image": BytesIO(b.getvalue()),
                "output_image": None,
                "image_description": None
            })

        # mark processing so UI doesn't allow re-start accidentally
        st.session_state.processing = True

        # Initialize client here (after validating key)
        try:
            client = genai.Client(api_key=api_key)
        except Exception as e:
            st.session_state.processing = False
            st.error(f"Failed to initialize Google client: {e}")
            return

        # Process images sequentially (you can parallelize later)
        my_bar = st.progress(0, text="Starting processing...")
        total = len(st.session_state.images)
        for idx in range(total):
            if not st.session_state.error_status["continue_processing"]:
                st.error(st.session_state.error_status["error_msg"])
                break

            # reopen BytesIO because previous PIL open might have consumed the stream
            img_stream = st.session_state.images[idx]["input_image"]
            img_stream.seek(0)
            try:
                generated = generate_image(img_stream, client=client)
            except Exception as e:
                # propagate into error_status so UI shows and processing stops gracefully
                st.session_state.error_status['continue_processing'] = False
                st.session_state.error_status['error_msg'] = f"Error while generating image: {e}"
                st.error(st.session_state.error_status['error_msg'])
                break

            if generated:
                st.session_state.images[idx]['output_image'] = generated.get("image")
                st.session_state.images[idx]['image_description'] = generated.get("text")

            # update progress
            my_bar.progress((idx + 1) / total, text=f"{idx+1}/{total} completed")

            # polite pause to avoid rate limits (you used 30s previously)
            if idx != total - 1:
                time.sleep(2)  # small pause; increase if you need to avoid throttling

        st.session_state.processing = False
        # show results
        image_display()


@st.fragment
def image_display():
    st.markdown("### Review Images")
    for i in range(len(st.session_state.images)):
        if st.session_state.images[i]['output_image'] is not None:
            with st.expander(label=f"Image {i+1}"):
                col1, col2 = st.columns(2, vertical_alignment="center")
                with col1:
                    # show input - seek first
                    inp = st.session_state.images[i]['input_image']
                    inp.seek(0)
                    st.image(inp)
                with col2:
                    out = st.session_state.images[i]['output_image']
                    if isinstance(out, BytesIO):
                        out.seek(0)
                        st.image(out)
                    else:
                        st.write("No output image to show")
        else:
            continue

    if st.session_state.error_status["continue_processing"] is True:
        st.markdown("### Regenerate Images")
        st.text("⚠️ Only try to regenerate images one at a time")
        col1, col2 = st.columns(2, vertical_alignment="bottom")
        with col1:
            image_id = st.number_input(label="Enter image number to regenerate",
                                       min_value=1, max_value=len(st.session_state.images), value=1)
        with col2:
            st.button(label="Regenerate image",
                      on_click=lambda: regenerate_image(image_id), type='primary')

    st.markdown("### Download Images")
    download_zip()


def generate_image(image, client=None):
    """
    generate_image now requires a client passed in to avoid re-initializing
    and to keep control in main().
    """
    MAX_RETRIES = 5
    attempts = 0

    # If client not provided, try to make one (defensive)
    if client is None:
        api_key = (st.session_state.get("api_key") or "").strip()
        if not api_key:
            raise RuntimeError("API key missing. Please enter your Google API key.")
        client = genai.Client(api_key=api_key)

    # make sure BytesIO at start
    if isinstance(image, BytesIO):
        image.seek(0)
        pil_img = PIL.Image.open(image).convert("RGB")
    else:
        pil_img = PIL.Image.open(image).convert("RGB")

    text_input = (
        'The given is an image of a piece of clothing. I want you to generate a ultrarealistic image of the clothing on a person.',
        'You must strictly make sure that the clothing is represented exactly how is given in the reference image.',
        'You must show the person completely from head to toe and if any necessary piece of clothing is missing (such as a bottom from an image of a top), you may add as appropriate.',
        'The generated image is to be used to display the item on an ecommerce website so keep that in mind when generating it.'
    )

    output = {"text": None, "image": None}
    last_error = None

    while attempts < MAX_RETRIES:
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[text_input, pil_img],
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE'],
                    temperature=0.5
                )
            )

            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    output["text"] = part.text
                elif part.inline_data is not None:
                    image_bytes = part.inline_data.data
                    output["image"] = BytesIO(image_bytes)

            return output

        except ClientError as e:
            last_error = e
            if str(e).startswith("429 RESOURCE_EXHAUSTED"):
                st.session_state.error_status['continue_processing'] = False
                st.session_state.error_status['error_msg'] = ("Your free tier quota is done for the day. "
                                                            "Please try tomorrow. All images already processed will be displayed below and available for download.")
                return output
            attempts += 1
            if attempts < MAX_RETRIES:
                time.sleep(5)
        except Exception as e:
            last_error = e
            attempts += 1
            if attempts < MAX_RETRIES:
                time.sleep(5)

    # if we reach here, too many attempts
    st.session_state.error_status['continue_processing'] = False
    st.session_state.error_status['error_msg'] = f"Too many errors: {last_error}"
    return output


def regenerate_image(image_id):
    image_index = int(image_id - 1)
    generated_data = generate_image(
        st.session_state.images[image_index]['input_image'])
    if st.session_state.error_status['continue_processing'] is True:
        st.session_state.images[image_index]['output_image'] = generated_data["image"]
        st.session_state.images[image_index]['image_description'] = generated_data["text"]
    else:
        with st.session_state.upload_container:
            st.error(
                st.session_state.error_status['error_msg'], icon="⚠️")


def download_zip():
    with BytesIO() as buffer:
        with zipfile.ZipFile(buffer, "w") as zip:
            for image in st.session_state.images:
                if image["output_image"] is not None:
                    zip.writestr(f"{image['image_id']}.png",
                                 image["output_image"].getvalue())
        buffer.seek(0)
        st.download_button(label="Download ZIP", data=buffer, type='primary',
                           icon=":material/download:", file_name="generated_images.zip", mime="application/zip")


main()
