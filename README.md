# LLM Clothes Modelling using Gemini API

## Introduction

Fashion e-commerce platforms often struggle to display garments realistically on human models without costly photoshoots. This project provides an AI-powered solution that generates ultra-realistic images of clothing items worn by virtual models, based on simple uploads of garment images.  

The system leverages **Google Gemini Image Generation API** to produce high-quality outputs that make the clothing appear exactly as in the reference image. If necessary, missing clothing items (like bottoms when only a top is provided) are intelligently added to produce a complete, ecommerce-ready model photo.  

Originally developed to help the NGO [AmarSaath](https://amarsaath.org/) sell second-hand clothes to raise funds for their causes, this tool has since been generalized for public use. It is cost-efficient and extensible, thanks to Gemini’s generous free tier. Users may also adapt the system to use other APIs or even local LLMs if desired.  

## Modules used

This project makes use of the following key modules:

- **streamlit** – for building the interactive web interface.
- **google-genai** – client library for Gemini API integration.
- **python-dotenv** – for environment variable management.
- **PIL (Pillow)** – for image processing.
- **zipfile** – for bundling generated images for download.
- **time** – for operation delays and retries.
- **io.BytesIO** – for in-memory image manipulation.

## Installation

To run the code in this repository, install the dependencies as follows:

1. Clone the repository:
   ```shell
   git clone <your-repo-url>
   ```
2. Navigate to the project directory:
   ```shell
   cd <your-project-folder>
   ```
3. Create a virtual environment (recommended) and activate it:
   ```shell
   python -m venv venv
   source venv/bin/activate   # On Linux/Mac
   venv\Scripts\activate      # On Windows
   ```
4. Install the dependencies:
   ```shell
   pip install -r requirements.txt
   ```

Dependencies include `streamlit`, `google-genai`, and `python-dotenv`.

## Steps Followed

### 1. Upload Clothing Images
Users upload up to 50 clothing images (`.jpg`, `.jpeg`, `.png`) through the **Streamlit UI**. These are cached for processing.

### 2. Image Generation
Each uploaded garment is processed via Gemini’s **image generation model (`gemini-2.0-flash-preview-image-generation`)**.  
The prompt ensures:
- The garment matches the reference image exactly.  
- The output shows a **full-body model** wearing the garment.  
- Missing complementary items (e.g., trousers for a shirt) are appropriately added.  
- The generated image is ecommerce-ready.  

### 3. Error Handling & Retries
- API calls retry up to **5 times** in case of errors.  
- If free-tier quota is exceeded, users are notified and can still download already generated images.  

### 4. Image Review & Regeneration
- Generated results are shown side-by-side with the uploaded images.  
- Users can **regenerate specific images** one at a time for improved outputs.  

### 5. Image Download
- A **ZIP file** of all generated model images can be downloaded directly.  

## Results

The application produces **ultra-realistic ecommerce-ready images** of clothing items on human models. These can be directly used by NGOs, small businesses, or individuals to showcase apparel without expensive photoshoots.

## Conclusion

This project demonstrates the practical use of **Generative AI in fashion e-commerce**, lowering barriers for organizations like NGOs or small sellers. While the current implementation uses **Google Gemini**, the architecture allows integration with other APIs or local models in the future.  

For NGOs such as [AmarSaath](https://amarsaath.org/), this project provides a sustainable way to showcase second-hand clothing for fundraising. For individuals and businesses, it opens up cost-effective opportunities to display apparel in a professional, realistic manner.  

For further details, refer to the codebase (`app.py`, `main.ipynb`) and inline documentation.  
Happy experimenting with AI-powered fashion modelling ❤️
