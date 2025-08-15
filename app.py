import streamlit as st


def main():
    import time

    st.image(image="logo.png", width=120)
    st.title("Amar Saath Clothes Modelling")

    upload_validation = False

    while not upload_validation:
        upload_container = st.empty()
        with upload_container:
            images = st.file_uploader(
                label='Upload clothing image here.', type=['jpeg', 'jpg', 'png'], accept_multiple_files=True, help="Maximum 50 files")
            if len(images) > 0 and len(images) > 50:
                st.toast("⚠️ Only 50 files can be processed at any given time!")
            else:
                upload_validation = True

    cache_images(images)

    if st.session_state.images != []:
        with upload_container:
            st.text("✅ Upload complete")
            for i in range(5, 0, -1):
                st.progress(0, f"⌛ Starting operation in {i}s")
                time.sleep(1)
            my_bar = st.progress(0, text="Operation starting. Please wait.")
        for i in range(len(st.session_state.images)):
            generated_data = generate_image(
                st.session_state.images[i]['input_image'])
            st.session_state.images[i]['output_image'] = generated_data["image"]
            st.session_state.images[i]['image_description'] = generated_data["text"]

            my_bar.progress(value=((i+1)/len(st.session_state.images)),
                            text=f"{i+1}/{len(st.session_state.images)} completed")

            if i != (len(st.session_state.images)-1):
                time.sleep(30)

        image_display()


@st.fragment
def image_display():
    st.markdown("### Review Images")
    for i in range(len(st.session_state.images)):
        with st.expander(label=f"Image {i+1}"):
            col1, col2 = st.columns(
                2, vertical_alignment="center")
            with col1:
                st.image(st.session_state.images[i]['input_image'])
            with col2:
                st.image(st.session_state.images[i]['output_image'])

    st.markdown("### Regenerate Images")
    st.text("⚠️ Only try to regenerate images one at a time")

    col1, col2 = st.columns(2, vertical_alignment="bottom")
    with col1:
        image_id = st.number_input(label="Enter image number to regenerate",
                                   min_value=1, max_value=len(st.session_state.images), placeholder="make sure you've got the right number!")
    with col2:
        st.button(label="Regenerate image",
                  on_click=lambda: regenerate_image(image_id), type='primary')


def cache_images(images):
    import io
    st.session_state.images = []

    for i in range(len(images)):
        st.session_state.images.append(
            {"image_id": f"Image {i+1}", "input_image": io.BytesIO(images[i].read()), "output_image": None, "image_description": None})


def regenerate_image(image_id):
    image_index = int(image_id - 1)
    generated_data = generate_image(
        st.session_state.images[image_index]['input_image'])
    st.session_state.images[image_index]['output_image'] = generated_data["image"]
    st.session_state.images[image_index]['image_description'] = generated_data["text"]


def generate_image(image):
    from google import genai
    from google.genai import types
    from io import BytesIO
    from dotenv import load_dotenv
    import os
    import PIL.Image

    load_dotenv()

    image = PIL.Image.open(image)

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    text_input = ('The given is an image of a piece of clothing. I want you to generate a ultrarealistic image of the clothing on a person.',
                  'You must strictly make sure that the clothing is represented exactly how is given in the reference image.',
                  'You must show the person completely from head to toe and if any necessary piece of clothing is missing (such as a bottom from an image of a top), you may add as appropriate.',
                  'The generated image is to be used to display the item on an ecommerce website so keep that in mind when generating it.')
    response = client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=[text_input, image],
        config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE'],
            temperature=0.5
        )
    )

    output = {"text": None, "image": None}
    for part in response.candidates[0].content.parts:
        if part.text is not None:
            output["text"] = part.text
        elif part.inline_data is not None:
            image = BytesIO((part.inline_data.data))
            output["image"] = image

    return output


main()
