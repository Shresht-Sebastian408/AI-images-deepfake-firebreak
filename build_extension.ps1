Write-Host "=========================================="
Write-Host "Packaging Chrome Extension for Web Store..."
Write-Host "=========================================="

$filesToInclude = @(
    "manifest.json",
    "background.js",
    "content.js",
    "content.css"
)

# Optional: Add icons folder if it exists in the future
if (Test-Path "icons") {
    $filesToInclude += "icons"
}

$destination = "ai_detector_extension_release.zip"

Write-Host "Zipping files: $($filesToInclude -join ', ')"
Compress-Archive -Path $filesToInclude -DestinationPath $destination -Force

Write-Host "`nSuccess! Created: $destination"
Write-Host "Do NOT include the 'backend' folder in your Chrome Web Store upload."
Write-Host "You can now upload $destination directly to the Chrome Developer Dashboard."
