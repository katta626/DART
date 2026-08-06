with tab2:
        def get_image_from_disk(path_to_image):
            """Load image from disk as PIL Image object."""
            return Image.open(path_to_image)

        def image_to_base64(img):
            if img:
                with BytesIO() as buffer:
                    img.save(buffer, "png")
                    raw_base64 = base64.b64encode(buffer.getvalue()).decode()
                    return f"data:image/png;base64,{raw_base64}"
        
        BASE_DIR = "/Users/naveenkatta/Downloads/DART/fits_plots"  # Each subfolder = Pulsar Name

        # --- Step 1: List available pulsars ---
        if not os.path.exists(BASE_DIR):
            print(f"Plots directory '{BASE_DIR}' not found.")

        pulsars = [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]
        if not pulsars:
            print("No pulsar folders found inside 'plots/'.")
        df = pd.DataFrame(columns=["Pulsar", "FITS", "PNG", "Observation Dates"])
        for selected_pulsar in pulsars:
            pulsar_dir = os.path.join(BASE_DIR, selected_pulsar)
            files = os.listdir(pulsar_dir)
            fits_files = [f for f in files if f.endswith(".fits")]
            png_files = [f for f in files if f.endswith(".png")]

            print(f"{selected_pulsar}: {len(fits_files)} FITS files, {len(png_files)} PNG files")
            for f in fits_files:
                match = re.search(r'(\d{2})_(\d{2})_(\d{4})', f)  
                if match:
                    day, month, year = match.groups()
                    print(f"File: {f} => Date: {day}-{month}-{year}")
                    image_path = pulsar_dir + "/" + f.replace(".fits", ".png")
                    image_path = image_to_base64(get_image_from_disk(image_path))
                    df.loc[len(df)] = [selected_pulsar ,f , image_path, f"{day}-{month}-{year}"]
                    
        st.data_editor(
                        df,
                        column_config={
                            "PNG": st.column_config.ImageColumn(
                                "Preview Image", help="Streamlit app preview screenshots",
                                width = "small"
                            )
                        },
                        hide_index=True
                    )
