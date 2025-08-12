import streamlit as st


def main():
    import time

    st.title("Clothes modelling application")
    images = st.file_uploader(
        label='Upload clothing image here.', type=['jpeg', 'jpg', 'png'], accept_multiple_files=True)
    st.session_state.images = images
    if st.session_state.images:
        for image in st.session_state.images:
            returned_image = get_model_image(image)
            st.image(returned_image)
            time.sleep(30)


def get_model_image(image):
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
            response_modalities=['TEXT', 'IMAGE']
        )
    )

    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            image = BytesIO((part.inline_data.data))
            return image


main()
