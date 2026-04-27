// background.js

// ----------------- CONFIGURATION -----------------
// Toggle this to true before you run the build script!
const IS_PRODUCTION = false;

// Once deployed, replace this with your real Google Cloud Run URL
const PROD_API_URL = "https://your-cloud-run-service.a.run.app/analyze";
const LOCAL_API_URL = "http://localhost:8000/analyze";

const API_URL = IS_PRODUCTION ? PROD_API_URL : LOCAL_API_URL;
// -------------------------------------------------

// This function now calls our local Python backend.
// Once you connect Vertex AI in your Python backend, this will automatically work end-to-end!
async function checkMediaWithAPI(url, type) {
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url: url, mediaType: type })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result = await response.json();
    return result;
  } catch (error) {
    // If the python server isn't running, just silently fail to not disrupt the user's browsing
    return { isAIGenerated: false, confidence: 0, type: type };
  }
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'analyze_media') {
    checkMediaWithAPI(request.url, request.mediaType)
      .then(result => sendResponse(result))
      .catch(error => {
        console.error("Error analyzing media:", error);
        sendResponse({ error: error.message });
      });
      
    // Return true to indicate we will send a response asynchronously
    return true; 
  }
});
