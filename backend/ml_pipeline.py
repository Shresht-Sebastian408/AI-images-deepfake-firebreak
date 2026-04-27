import cv2
import numpy as np
import warnings

try:
    import tensorflow as tf
    from tensorflow.keras import layers, models
    TF_AVAILABLE = True
except ImportError:
    print("⚠️ WARNING: TensorFlow could not be imported (likely due to Python 3.14 incompatibility).")
    print("⚠️ The 2D FFT will still run, but CNN inference will be mocked.")
    TF_AVAILABLE = False

def extract_high_frequencies(frame, r=50):
    """
    Applies 2D FFT and masks the low-frequency center.
    Args:
        frame: Raw BGR or Gray image frame.
        r: radius of the high-pass filter mask.
    Returns:
        magnitude_spectrum of the high-frequency components.
    """
    # Convert to grayscale
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame

    # Apply 2D FFT
    f_transform = np.fft.fft2(gray)
    f_transform_shifted = np.fft.fftshift(f_transform)

    # High-pass filter: mask for the center (low frequencies)
    rows, cols = gray.shape
    crow, ccol = rows // 2, cols // 2
    f_transform_shifted[crow-r:crow+r, ccol-r:ccol+r] = 0

    # Calculate Magnitude Spectrum
    magnitude_spectrum = 20 * np.log(np.abs(f_transform_shifted) + 1e-8)
    
    # Normalize to [0, 255] for CNN input
    magnitude_spectrum = cv2.normalize(magnitude_spectrum, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    return magnitude_spectrum

def create_spectral_cnn(input_shape=(256, 256, 1)):
    """
    Creates a CNN suitable for processing frequency domain feature maps.
    """
    if not TF_AVAILABLE:
        return None
        
    model = models.Sequential([
        layers.InputLayer(input_shape=input_shape),
        
        # Convolutional Block 1
        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.BatchNormalization(),
        
        # Convolutional Block 2
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.BatchNormalization(),
        
        # Deep Feature Extraction
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        
        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.5), # Regularization
        layers.Dense(1, activation='sigmoid') # Real (0) vs. Synthetic (1)
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

# Initialize the model globally so it's only built once when the server starts
if TF_AVAILABLE:
    print("Initializing Spectral CNN architecture...")
    spectral_model = create_spectral_cnn()
    print("Spectral CNN initialized.")
else:
    spectral_model = None

def process_and_predict(image_bytes):
    """
    Takes raw image bytes, runs the 2D FFT preprocessing, and performs inference.
    """
    # 1. Decode image bytes to OpenCV format
    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    if frame is None:
        raise ValueError("Could not decode image bytes.")
        
    # 2. Extract high frequencies using 2D FFT
    magnitude_spectrum = extract_high_frequencies(frame)
    
    # 3. Resize to match CNN input shape (256, 256)
    resized_spectrum = cv2.resize(magnitude_spectrum, (256, 256))
    
    # 4. Reshape and normalize for inference
    if TF_AVAILABLE:
        input_tensor = resized_spectrum.reshape(1, 256, 256, 1).astype('float32') / 255.0
        
        # 5. Run Inference
        prediction = spectral_model.predict(input_tensor, verbose=0)
        confidence = float(prediction[0][0])
    else:
        import random
        confidence = random.uniform(0.01, 0.99)
        print("CNN Inference Mocked (TF unavailable).")
        
    return confidence
