import numpy as np
from PIL import Image, ImageOps
import streamlit as st
import io
from rembg import remove
from filters.filters import apply_filters
from filters.sketch import apply_sketch
from filters.dithering import apply_dithering
from filters.tracing import apply_tracing, tracing_options
from filters.webp_to_png import main as webp_converter
from filters.enhance_with_pil import enhance_image_pil, auto_enhance_image
from PIL import ImageStat
import cv2

def enhance_main(image):
    # Αρχική αποθήκευση εικόνας για το preset_result
    if "preset_result" not in st.session_state:
        st.session_state.preset_result = image

    st.subheader("🎨 Portrait Enhancer")

    with st.sidebar:
        st.markdown("### 🧰 Settings")
        mode = st.radio("Enhancement Mode", ["Preset", "Manual"])

        if mode == "Preset":
            style = st.selectbox("Retouch Style", ["Natural", "Soft Studio", "Glow Mode", "High Glam"])
            intensity = st.slider("Intensity", 0.5, 7.0, 1.0, 0.1)
            smoothness = st.slider("Skin Smoothing", 0, 200, 50, 5)
            clarity = st.slider("Sharpness Boost", 0.0, 4.0, 1.0, 0.1)

            result = auto_enhance_image(
                image,
                style=style,
                intensity=intensity,
                smoothness=smoothness,
                clarity=clarity
            )

            # Αποθήκευση του αποτελέσματος preset στη μνήμη
            st.session_state.preset_result = result

        else:
            # Χρησιμοποιούμε το αποτέλεσμα από preset ως βάση
            base_image = st.session_state.preset_result

            sharpness = st.slider("Sharpness", 0.0, 5.0, 1.5, step=0.1)
            contrast = st.slider("Contrast", 0.5, 1.5, 1.0, step=0.05)
            brightness = st.slider("Brightness", 0.5, 1.5, 1.0, step=0.05)
            saturation = st.slider("Saturation", 0.5, 2.0, 1.0, step=0.1)

            result = enhance_image_pil(
                base_image,
                sharpness=sharpness,
                contrast=contrast,
                brightness=brightness,
                saturation=saturation
            )

    # Εμφάνιση εικόνων
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.image(ImageOps.contain(image, (600, 600)), caption="📷 Original", width=600)
    with col2:
        st.image(ImageOps.contain(result, (600, 600)), caption="✨ Enhanced", width=600)
    
       
        # Αποθήκευση
    buf = io.BytesIO()
    result.save(buf, format="PNG")
    st.download_button("💾 Save Image", buf.getvalue(), file_name="enhanced.png", mime="image/png")

def main():
    if "show_help" not in st.session_state:
        st.session_state.show_help = False
    
    st.set_page_config(layout="wide", page_title="Image Processor By Anthony Zacharioudakis Ver. 0.21")
    st.title("🖼️ Image processing for Laser & SVG")

    if "mode" not in st.session_state:
        st.session_state.mode = "editor"

    uploaded_file = st.sidebar.file_uploader("📂 Upload", type=["png", "jpg", "jpeg"])
    uploaded_image = None
    if uploaded_file is not None:
        uploaded_image = Image.open(uploaded_file).convert("RGB")

    if st.session_state.mode == "enhance":
        st.button("⬅️ Return to Image editor", on_click=lambda: st.session_state.update({"mode": "editor"}))
        st.markdown("---")
        if uploaded_image:
            enhance_main(uploaded_image)
        else:
            st.info("📥 First upload image from sidebar.")
        st.stop()

    #if st.button("🪄 Enhance image", key="enhance_button"):
       # st.session_state.mode = "enhance"

    if st.session_state.mode == "webp":
        st.button("⬅️ Return", on_click=lambda: st.session_state.update({"mode": "editor"}))
        st.markdown("---")
        webp_converter()
        st.stop()

    #if st.button("➕ Convert WEBP to PNG"):
        #st.session_state.mode = "webp"
        #st.stop()
    col1, col2 , col3 = st.columns(3)

    with col1:
        if st.button("🪄 Enhance image double click", key="enhance_button"):
            st.session_state.mode = "enhance"


    with col2:
        if st.button("➕  WEBP to PNG double click "):
            st.session_state.mode = "webp"
            st.stop()

    with col3:
        if st.button("📘 Online help"):
            st.session_state.show_help = not st.session_state.show_help


                
    if st.session_state.show_help:
        try:
            with open("help.md", "r", encoding="utf-8") as f:
                st.markdown(f.read(), unsafe_allow_html=True)
        except FileNotFoundError:
            st.error("File not found.")

    
    
    if uploaded_file is not None:
        original_image = Image.open(uploaded_file)
        if "icc_profile" in original_image.info:
            del original_image.info["icc_profile"]
        original_image = original_image.convert("RGBA")

        if "removed_bg_image" not in st.session_state:
            st.session_state.removed_bg_image = None

        if st.sidebar.button("🧹 Remove Background"):
            try:
                buffer = io.BytesIO()
                original_image.save(buffer, format="PNG")
                buffer.seek(0)
                output_data = remove(buffer.getvalue())
                st.session_state.removed_bg_image = Image.open(io.BytesIO(output_data)).convert("RGBA")
                st.success("✅ Background removed.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

        processed_image = st.session_state.removed_bg_image or original_image
        svg_output = None

        tab1, tab2, tab3, tab4 = st.tabs(["🎛️ Filters", "✏️ Sketch", "🧊 Dithering", "🧬 Outline"])

        with tab1:
            st.subheader("Filter adjustment")
            c1, c2, c3 = st.columns(3)
            with c1:
                contrast = st.slider("Contrast", 0.5, 2.0, 1.0, 0.1)
            with c2:
                brightness = st.slider("Brightness", 0.5, 2.0, 1.0, 0.1)
            with c3:
                saturation = st.slider("Saturation", 0.0, 2.0, 1.0, 0.1)
            processed_image = apply_filters(processed_image, contrast, brightness, saturation)

        with tab2:
            st.subheader("Pencil sketch")
            if st.button("Apply sketch"):
                processed_image = apply_sketch(processed_image)

        with tab3:
            st.subheader("Dithering")
            if st.button("Jarvis Dither"):
                processed_image = apply_dithering(processed_image, algorithm="jarvis")
            if st.button("Stucki Dither"):
                processed_image = apply_dithering(processed_image, algorithm="stucki")

        with tab4:
            st.subheader("Trace outline & SVG")
            trace_enabled = st.checkbox("Enable preview")

            if trace_enabled:
                col1, col2 = st.columns([2, 3])
                with col1:
                    mode = st.selectbox("Method", ["potrace", "opencv"])
                    threshold = st.slider("Threshold", 0, 255, 180)
                    threshold2 = st.slider("Threshold 2", 0, 255, 150)
                    invert = tracing_options()

                    preview_image, svg_output = apply_tracing(
                        processed_image,
                        mode=mode,
                        threshold=threshold,
                        threshold2=threshold2,
                        thickness=1,
                        invert=invert
                    )

                with col2:
                    st.image(ImageOps.contain(preview_image, (500, 500)), caption="Trace Preview", use_container_width=True)

                    if svg_output:
                        st.download_button(
                            label="📥 Download SVG",
                            data=svg_output,
                            file_name="traced_image.svg",
                            mime="image/svg+xml"
                        )

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.header("🖼️ Original")
            st.image(ImageOps.contain(original_image, (600, 600)), use_container_width=True)

        with col2:
            st.header("✨ Edited")
            st.image(ImageOps.contain(processed_image, (600, 600)), use_container_width=True)

            img_buffer = io.BytesIO()
            processed_image.convert("RGBA").save(img_buffer, format="PNG")
            st.download_button(
                label="📥 Download PNG",
                data=img_buffer.getvalue(),
                file_name="no_bg_image.png",
                mime="image/png"
            )

if __name__ == "__main__":
    main()
