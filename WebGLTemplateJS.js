// WebGLTemplateJS.js - Chunk 1: Core Initialization and Setup

// Global variables for state management
var mapData = null;
var unityInstance = null;
var azgaarFrame = null;
var azgaarLoaded = false;
var updateInterval = null;
var updateFrequency = 1000; // Default: 1 second
var azgaarBaseUrl = "https://azgaar.github.io/Fantasy-Map-Generator/";
var debugMode = false;

/**
 * Initializes the Azgaar Fantasy Map Generator viewer with the specified map data
 * This function is called from Unity via the DllImport interface
 *
 * @param {string} mapDataStr - The raw map data as a string
 * @param {boolean} enableEditing - Whether to enable map editing
 * @param {boolean} disableGeneration - Whether to disable map generation features
 * @param {number} updateFreq - How frequently to update the texture (in seconds)
 * @param {string} customUrl - Optional custom URL for the Azgaar viewer
 */
function InitializeAzgaarMapViewer(mapDataStr, enableEditing, disableGeneration, updateFreq, customUrl) {
    // Store map data
    mapData = mapDataStr;

    // Configure update frequency
    updateFrequency = updateFreq * 1000 || 1000; // Convert to milliseconds

    // Use custom URL if provided
    if (customUrl && customUrl.trim() !== "") {
        azgaarBaseUrl = customUrl;
    }

    // Log initialization
    logDebug("Initializing Azgaar map viewer");
    logDebug(`Settings: editing=${enableEditing}, disableGen=${disableGeneration}, updateFreq=${updateFrequency}ms`);

    // Get the iframe element
    azgaarFrame = document.getElementById('azgaar-frame');
    if (!azgaarFrame) {
        logError("Azgaar iframe not found in the DOM");
        return;
    }

    // Load the Azgaar Fantasy Map Generator
    azgaarFrame.src = azgaarBaseUrl;

    // Wait for the iframe to load
    azgaarFrame.onload = function() {
        logDebug("Azgaar iframe loaded");

        // Apply configuration classes
        try {
            if (!enableEditing) {
                azgaarFrame.contentDocument.body.classList.add('no-editing');
                logDebug("Editing disabled");
            }

            if (disableGeneration) {
                azgaarFrame.contentDocument.body.classList.add('no-generation');
                logDebug("Generation disabled");
            }
        } catch (e) {
            logError("Error applying configuration classes: " + e.message);
        }

        // Setup and load map with retries
        setupAzgaarWithRetries(5);
    };
}

/**
 * Attempts to set up the Azgaar map with retries on failure
 *
 * @param {number} maxRetries - Maximum number of retry attempts
 * @param {number} attempt - Current attempt number (internal use)
 * @param {number} delay - Delay between attempts in ms (internal use)
 */
function setupAzgaarWithRetries(maxRetries, attempt = 1, delay = 1000) {
    logDebug(`Setting up Azgaar (attempt ${attempt}/${maxRetries})`);

    try {
        // Access the Azgaar app's window
        var azgaarWindow = azgaarFrame.contentWindow;

        // Check if the Azgaar app is ready
        if (typeof azgaarWindow.uploadMap !== 'function') {
            if (attempt < maxRetries) {
                // Retry after delay
                logDebug(`Azgaar not ready yet, retrying in ${delay}ms...`);
                setTimeout(function() {
                    setupAzgaarWithRetries(maxRetries, attempt + 1, delay * 1.5);
                }, delay);
            } else {
                logError("Failed to initialize Azgaar after maximum retries");
            }
            return;
        }

        // Successfully connected to Azgaar
        logDebug("Connected to Azgaar successfully");

        // Configure the map features
        configureMapFeatures(azgaarWindow);

        // Load the map data
        loadMapData(azgaarWindow, mapData);

        // Set up communication between Unity and Azgaar
        setupCommunication(azgaarWindow);

        // Start capturing canvas for Unity display
        startCaptureCanvas(azgaarWindow);

        // Mark as loaded
        azgaarLoaded = true;

    } catch (e) {
        logError("Error in setupAzgaar: " + e.message);

        if (attempt < maxRetries) {
            // Retry after delay
            setTimeout(function() {
                setupAzgaarWithRetries(maxRetries, attempt + 1, delay * 1.5);
            }, delay);
        }
    }
}

/**
 * Configures map features based on settings
 *
 * @param {Window} azgaarWindow - The Azgaar app window
 */
function configureMapFeatures(azgaarWindow) {
    try {
        // Hide generation-related controls if needed
        if (azgaarWindow.document.body.classList.contains('no-generation')) {
            // Hide generation buttons and menus
            var generationElements = azgaarWindow.document.querySelectorAll(
                '#generateButton, #regenerateButton, #rescaleButton'
            );

            generationElements.forEach(function(element) {
                if (element) element.style.display = 'none';
            });

            // Modify the menu to remove generation options
            var menuItems = azgaarWindow.document.querySelectorAll('#menu > button');
            menuItems.forEach(function(item) {
                if (item && (item.textContent.includes('Generate') ||
                   item.textContent.includes('New Map'))) {
                    item.style.display = 'none';
                }
            });

            logDebug("Generation controls hidden");
        }

        // Hide editing controls if needed
        if (azgaarWindow.document.body.classList.contains('no-editing')) {
            // TODO: Implement edit control hiding if needed
        }
    } catch (e) {
        logError("Error configuring map features: " + e.message);
    }
}

/**
 * Utility function for debug logging
 *
 * @param {string} message - The message to log
 */
function logDebug(message) {
    if (debugMode) {
        console.log("[AzgaarBridge] " + message);
    }
}

/**
 * Utility function for error logging
 *
 * @param {string} message - The error message to log
 */
function logError(message) {
    console.error("[AzgaarBridge] ERROR: " + message);
    // Could also send errors to Unity here
}
// WebGLTemplateJS.js - Chunk 2: Map Loading and Communication

/**
 * Loads the map data into Azgaar
 *
 * @param {Window} azgaarWindow - The Azgaar app window
 * @param {string} mapData - The map data to load
 */
function loadMapData(azgaarWindow, mapData) {
    if (!mapData) {
        logError("No map data provided");
        return false;
    }

    try {
        logDebug("Preparing to load map data");

        // Create a temporary file containing the map data
        var blob = new Blob([mapData], {type: 'application/octet-stream'});
        var file = new File([blob], "unity_map.map", {type: 'application/octet-stream'});

        // Try different loading approaches
        return loadMapWithFallbacks(azgaarWindow, file);
    } catch (e) {
        logError("Error preparing map data: " + e.message);
        return false;
    }
}

/**
 * Attempts to load the map file using various methods with fallbacks
 *
 * @param {Window} azgaarWindow - The Azgaar app window
 * @param {File} file - The map file to load
 * @returns {boolean} - Whether the load was successful
 */
function loadMapWithFallbacks(azgaarWindow, file) {
    // Method 1: Try using Azgaar's native uploadFile function
    if (typeof azgaarWindow.uploadFile === 'function') {
        logDebug("Loading map using uploadFile method");
        try {
            azgaarWindow.uploadFile(file);
            logDebug("Map loaded successfully using uploadFile");
            return true;
        } catch (e) {
            logDebug("uploadFile method failed: " + e.message);
            // Continue to next method
        }
    }

    // Method 2: Try using uploadMap function
    if (typeof azgaarWindow.uploadMap === 'function') {
        logDebug("Loading map using uploadMap method");
        try {
            azgaarWindow.uploadMap(file);
            logDebug("Map loaded successfully using uploadMap");
            return true;
        } catch (e) {
            logDebug("uploadMap method failed: " + e.message);
            // Continue to next method
        }
    }

    // Method 3: Use DOM simulation as a last resort
    logDebug("Loading map using DOM simulation method");
    try {
        // Create a temporary input and trigger a change event
        var fileInput = azgaarWindow.document.createElement('input');
        fileInput.type = 'file';
        fileInput.style.display = 'none';

        // Create a DataTransfer object to hold our file
        var dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;

        // Append to document and trigger change event
        azgaarWindow.document.body.appendChild(fileInput);

        // Create and dispatch a change event
        var changeEvent = new Event('change', {bubbles: true});
        fileInput.dispatchEvent(changeEvent);

        // Clean up
        setTimeout(function() {
            azgaarWindow.document.body.removeChild(fileInput);
            logDebug("Map loading attempted using DOM simulation");
        }, 1000);

        return true; // We can't be sure this worked, but we tried
    } catch (e) {
        logError("All map loading methods failed: " + e.message);
        return false;
    }
}

/**
 * Set up communication between Unity and Azgaar
 * Exposes methods that Unity can call to interact with the map
 *
 * @param {Window} azgaarWindow - The Azgaar app window
 */
function setupCommunication(azgaarWindow) {
    logDebug("Setting up Unity-Azgaar communication bridge");

    // Allow Unity to send commands to Azgaar
    window.UpdateMapView = function(commandStr) {
        if (!azgaarLoaded) {
            logError("Cannot update map: Azgaar not loaded yet");
            return;
        }

        try {
            var parts = commandStr.split('|');
            var command = parts[0];

            logDebug("Received command: " + command);

            switch(command) {
                case "toggleLayer":
                    var layerName = parts[1];
                    var visible = parts[2] === "true";
                    toggleLayerVisibility(azgaarWindow, layerName, visible);
                    break;

                case "zoomTo":
                    var x = parseFloat(parts[1]);
                    var y = parseFloat(parts[2]);
                    var zoom = parseFloat(parts[3]);
                    zoomToCoordinates(azgaarWindow, x, y, zoom);
                    break;

                case "resetView":
                    resetView(azgaarWindow);
                    break;

                default:
                    logError("Unknown command: " + command);
            }
        } catch (e) {
            logError("Error processing command: " + e.message);
        }
    };

    // Allow Unity to get the current map data
    window.GetMapData = function() {
        if (!azgaarLoaded) {
            logError("Cannot get map data: Azgaar not loaded yet");
            return "";
        }

        try {
            // Access Azgaar's save function to get the current map data
            if (typeof azgaarWindow.saveMap === 'function') {
                // This would ideally return the map data, but we need a workaround
                // as Azgaar might trigger a download instead

                // For now, we'll return the original map data
                // In a full implementation, we'd hook into Azgaar's save process
                return mapData;
            }
        } catch (e) {
            logError("Error getting map data: " + e.message);
        }

        return mapData; // Return original data as fallback
    };

    // Get information about the current map
    window.GetMapInfo = function() {
        if (!azgaarLoaded) {
            logError("Cannot get map info: Azgaar not loaded yet");
            return "{}";
        }

        try {
            // Get information based on what's available in the Azgaar API
            var info = {
                ready: azgaarLoaded,
                timestamp: new Date().toISOString()
            };

            // Try to add map name if available
            if (azgaarWindow.mapName) {
                info.name = azgaarWindow.mapName;
            }

            return JSON.stringify(info);
        } catch (e) {
            logError("Error getting map info: " + e.message);
            return JSON.stringify({ error: e.message });
        }
    };
}

/**
 * Starts capturing the Azgaar canvas at regular intervals
 *
 * @param {Window} azgaarWindow - The Azgaar app window
 */
function startCaptureCanvas(azgaarWindow) {
    try {
        // Find the main canvas element
        var canvas = azgaarWindow.document.getElementById('map');
        if (!canvas) {
            logError("Azgaar map canvas not found");
            return;
        }

        // Clear any existing interval
        if (updateInterval) {
            clearInterval(updateInterval);
        }

        // Set up a timer to periodically capture the canvas
        updateInterval = setInterval(function() {
            captureAndSendCanvas(azgaarWindow, canvas);
        }, updateFrequency);

        logDebug(`Canvas capture started (every ${updateFrequency}ms)`);
    } catch (e) {
        logError("Error starting canvas capture: " + e.message);
    }
}

/**
 * Captures the canvas and sends it to Unity
 *
 * @param {Window} azgaarWindow - The Azgaar app window
 * @param {HTMLCanvasElement} canvas - The canvas element to capture
 */
function captureAndSendCanvas(azgaarWindow, canvas) {
    try {
        // Convert canvas to data URL
        var dataUrl = canvas.toDataURL('image/png');

        // Convert data URL to binary data
        var binaryData = atob(dataUrl.split(',')[1]);
        var length = binaryData.length;
        var bytes = new Uint8Array(length);

        for (var i = 0; i < length; i++) {
            bytes[i] = binaryData.charCodeAt(i);
        }

        // Update Unity texture
        if (unityInstance) {
            unityInstance.SendMessage('AzgaarMapDisplay', 'UpdateTextureFromJS', bytes);
        }
    } catch (e) {
        logError("Error capturing canvas: " + e.message);
    }
}
// WebGLTemplateJS.js - Chunk 3: Map Manipulation Methods

/**
 * Toggles the visibility of a specific map layer
 *
 * @param {Window} azgaarWindow - The Azgaar app window
 * @param {string} layerName - The name of the layer to toggle
 * @param {boolean} visible - Whether the layer should be visible
 */
function toggleLayerVisibility(azgaarWindow, layerName, visible) {
    try {
        logDebug(`Toggling layer '${layerName}' visibility to ${visible}`);

        // Method 1: Try direct element ID approach
        var layer = azgaarWindow.document.getElementById(layerName);
        if (layer) {
            layer.style.display = visible ? 'block' : 'none';
            logDebug(`Layer '${layerName}' toggled via direct ID method`);
            return;
        }

        // Method 2: Try accessing via Azgaar's API if available
        if (typeof azgaarWindow.toggleLayer === 'function') {
            azgaarWindow.toggleLayer(layerName, visible);
            logDebug(`Layer '${layerName}' toggled via API method`);
            return;
        }

        // Method 3: Try querySelector approach for common layer types
        const layerClasses = {
            'biomes': '#biomes',
            'relief': '#relief',
            'rivers': '#rivers',
            'routes': '#routes',
            'borders': '#borders',
            'labels': '#labels',
            'markers': '#markers'
        };

        if (layerClasses[layerName]) {
            var layerElement = azgaarWindow.document.querySelector(layerClasses[layerName]);
            if (layerElement) {
                layerElement.style.display = visible ? 'block' : 'none';
                logDebug(`Layer '${layerName}' toggled via querySelector method`);
                return;
            }
        }

        logError(`Could not find layer '${layerName}' to toggle visibility`);
    } catch (e) {
        logError(`Error toggling layer '${layerName}' visibility: ${e.message}`);
    }
}

/**
 * Zooms to specific coordinates on the map
 *
 * @param {Window} azgaarWindow - The Azgaar app window
 * @param {number} x - X coordinate
 * @param {number} y - Y coordinate
 * @param {number} zoom - Zoom level
 */
function zoomToCoordinates(azgaarWindow, x, y, zoom) {
    try {
        logDebug(`Zooming to (${x}, ${y}) at zoom level ${zoom}`);

        // Method 1: Try Azgaar's zoomTo function
        if (typeof azgaarWindow.zoomTo === 'function') {
            azgaarWindow.zoomTo(x, y, zoom);
            logDebug("Zoom performed via zoomTo API method");
            return;
        }

        // Method 2: Try accessing the viewbox if API method isn't available
        var svg = azgaarWindow.document.querySelector('svg');
        if (svg) {
            // Calculate viewbox values based on coordinates and zoom
            // This is an approximation and would need to be calibrated
            var viewboxWidth = 1000 / zoom;
            var viewboxHeight = 1000 / zoom;

            var viewboxX = x - viewboxWidth / 2;
            var viewboxY = y - viewboxHeight / 2;

            svg.setAttribute('viewBox', `${viewboxX} ${viewboxY} ${viewboxWidth} ${viewboxHeight}`);
            logDebug("Zoom performed via SVG viewBox method");
            return;
        }

        logError("Could not perform zoom: No compatible method found");
    } catch (e) {
        logError(`Error zooming to coordinates: ${e.message}`);
    }
}

/**
 * Resets the map view to its default state
 *
 * @param {Window} azgaarWindow - The Azgaar app window
 */
function resetView(azgaarWindow) {
    try {
        logDebug("Resetting map view");

        // Method 1: Try Azgaar's resetZoom function
        if (typeof azgaarWindow.resetZoom === 'function') {
            azgaarWindow.resetZoom();
            logDebug("View reset via resetZoom API method");
            return;
        }

        // Method 2: Try reset using viewbox if API method isn't available
        var svg = azgaarWindow.document.querySelector('svg');
        if (svg) {
            // Use default viewbox values
            svg.setAttribute('viewBox', '0 0 1000 1000');
            logDebug("View reset via SVG viewBox method");
            return;
        }

        logError("Could not reset view: No compatible method found");
    } catch (e) {
        logError(`Error resetting view: ${e.message}`);
    }
}

/**
 * Gets information about specific map elements
 *
 * @param {Window} azgaarWindow - The Azgaar app window
 * @param {string} elementType - Type of element to get info about (e.g., "states", "provinces")
 * @returns {Object|null} Information about the requested elements, or null on error
 */
function getMapElementInfo(azgaarWindow, elementType) {
    try {
        logDebug(`Getting info about map elements: ${elementType}`);

        // This is a placeholder for actual implementation
        // In a real implementation, we would access Azgaar's data structures
        // to get information about the requested elements

        return null;
    } catch (e) {
        logError(`Error getting map element info: ${e.message}`);
        return null;
    }
}

/**
 * Handles cleanup when the page is unloaded
 */
function cleanup() {
    try {
        // Stop canvas capturing
        if (updateInterval) {
            clearInterval(updateInterval);
            updateInterval = null;
        }

        logDebug("Cleanup completed");
    } catch (e) {
        logError(`Error during cleanup: ${e.message}`);
    }
}

// Register cleanup handler
window.addEventListener('beforeunload', cleanup);

// Debug mode setting - change this to enable detailed logging
debugMode = true;