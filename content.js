// content.js

// Set to keep track of processed media elements to avoid re-processing
const processedMedia = new WeakSet();

// Minimum dimensions to check (ignore tiny icons/tracking pixels)
const MIN_WIDTH = 100;
const MIN_HEIGHT = 100;

function analyzeMediaElement(element) {
  if (processedMedia.has(element)) return;
  processedMedia.add(element);

  // Get the URL
  const url = element.src || element.currentSrc || element.poster;
  if (!url || url.startsWith('data:')) return; // Skip base64 images for now

  const mediaType = element.tagName.toLowerCase() === 'img' ? 'image' : 'video';

  // Wait for the image/video to load slightly so we have dimensions
  if (element.tagName === 'IMG' && !element.complete) {
    element.addEventListener('load', () => processElementWithDimensions(element, url, mediaType), { once: true });
  } else {
    processElementWithDimensions(element, url, mediaType);
  }
}

function processElementWithDimensions(element, url, mediaType) {
  // Check dimensions
  const rect = element.getBoundingClientRect();
  const width = element.naturalWidth || element.videoWidth || rect.width;
  const height = element.naturalHeight || element.videoHeight || rect.height;

  if (width < MIN_WIDTH || height < MIN_HEIGHT) return;

  // Send to background for analysis
  chrome.runtime.sendMessage(
    { action: 'analyze_media', url: url, mediaType: mediaType },
    (response) => {
      if (chrome.runtime.lastError) {
         // Background script might not be ready, ignore.
         return;
      }
      if (response && response.isAIGenerated) {
        addWarningOverlay(element, response.confidence);
      }
    }
  );
}

function addWarningOverlay(element, confidence) {
  // 1. Add a glowing red border to the image/video itself
  element.classList.add('ai-detector-flagged-media');
  
  // 2. Add a global toast notification if not already present
  let toastContainer = document.getElementById('ai-detector-toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'ai-detector-toast-container';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  toast.className = 'ai-detector-toast';
  
  const icon = document.createElement('div');
  icon.className = 'ai-detector-toast-icon';
  icon.innerHTML = '🤖';

  const content = document.createElement('div');
  content.className = 'ai-detector-toast-content';
  
  const title = document.createElement('div');
  title.className = 'ai-detector-toast-title';
  title.innerText = 'AI Media Detected';

  const desc = document.createElement('div');
  desc.className = 'ai-detector-toast-desc';
  desc.innerText = `${element.tagName === 'IMG' ? 'Image' : 'Video'} flagged with ${(confidence * 100).toFixed(0)}% confidence.`;

  content.appendChild(title);
  content.appendChild(desc);
  toast.appendChild(icon);
  toast.appendChild(content);

  // Button to scroll to the element
  const actionBtn = document.createElement('button');
  actionBtn.className = 'ai-detector-toast-btn';
  actionBtn.innerText = 'View';
  actionBtn.onclick = () => {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    // Flash the border to highlight
    element.style.animation = 'none';
    setTimeout(() => {
      element.style.animation = 'ai-detector-pulse 1s 3';
    }, 50);
  };
  toast.appendChild(actionBtn);

  toastContainer.appendChild(toast);

  // Remove toast after 6 seconds
  setTimeout(() => {
    toast.classList.add('ai-detector-toast-hide');
    setTimeout(() => toast.remove(), 500); // Wait for transition
  }, 6000);
}

// Observe DOM for new elements
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.addedNodes) {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE) {
          if (node.tagName === 'IMG' || node.tagName === 'VIDEO') {
            analyzeMediaElement(node);
          }
          // Also search within the added node
          const mediaEls = node.querySelectorAll('img, video');
          mediaEls.forEach(analyzeMediaElement);
        }
      });
    }
  });
});

observer.observe(document.body, {
  childList: true,
  subtree: true
});

// Process existing elements on load
document.querySelectorAll('img, video').forEach(analyzeMediaElement);
