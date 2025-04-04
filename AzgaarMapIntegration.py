// AzgaarMapIntegration.cs
using
UnityEngine;
using
System;
using
System.IO;
using
System.Collections;
using
UnityEngine.UI;
using
System.Runtime.InteropServices;

// / < summary >
// / Core
component
that
integrates
Azgaar
's Fantasy Map Generator with Unity.
// / Handles
map
loading, display, and interaction
between
Unity and the
map
viewer.
// / < / summary >
[RequireComponent(typeof(RawImage))]
public


class AzgaarMapIntegration: MonoBehaviour


{
    # region Configuration

    [Header("Map Settings")]
    [Tooltip("Path to the Azgaar map file (.map)")]
    [SerializeField]
private
string
mapFilePath = string.Empty;

[Tooltip("Enable to allow editing the map")]
[SerializeField]
private
bool
enableMapEditing = true;

[Tooltip("Enable to prevent generating new maps")]
[SerializeField]
private
bool
disableGeneration = true;

[Header("Display Settings")]
[Tooltip("Width of the WebGL texture in pixels")]
[SerializeField]
private
int
textureWidth = 1280;

[Tooltip("Height of the WebGL texture in pixels")]
[SerializeField]
private
int
textureHeight = 720;

[Tooltip("Update frequency in seconds (lower values = smoother updates but higher CPU usage)")]
[Range(0.1
f, 5
f)]
[SerializeField]
private
float
updateFrequency = 1.0
f;

[Header("Advanced Options")]
[Tooltip("Custom URL for Azgaar Fantasy Map Generator (leave empty for default)")]
[SerializeField]
private
string
customAzgaarUrl = string.Empty;

[Tooltip("Enable detailed debug logging")]
[SerializeField]
private
bool
enableDebugLogging = false;

# endregion

# region Component References

private
RawImage
displayImage;
private
MapTextureManager
textureManager;

# endregion

# region JavaScript Interface Methods

[DllImport("__Internal")]
private
static
extern
void
InitializeAzgaarMapViewer(string
mapData, bool
enableEditing,
bool
disableGeneration, float
updateFrequency,
string
customUrl);

[DllImport("__Internal")]
private
static
extern
void
UpdateMapView(string
command);

[DllImport("__Internal")]
private
static
extern
string
GetMapData();

[DllImport("__Internal")]
private
static
extern
string
GetMapInfo();

# endregion

# region Unity Lifecycle Methods

private
void
Awake()
{
    displayImage = GetComponent < RawImage > ();
textureManager = new
MapTextureManager(textureWidth, textureHeight);

LogDebug("AzgaarMapIntegration initialized");
}

private
void
Start()
{
// Set
initial
texture
if (displayImage != null & & textureManager != null)
{
    displayImage.texture = textureManager.Texture;
LogDebug("Display texture initialized");
}

// Load
the
map
StartCoroutine(LoadMapRoutine());
}

# endregion

# region Public API

// / < summary >
// / Toggles
the
visibility
of
a
specific
map
layer
// / < / summary >
// / < param
name = "layerName" > Name
of
the
layer(e.g., "biomes", "rivers", "borders") < / param >
// / < param
name = "visible" > Whether
the
layer
should
be
visible < / param >
            public
void
ToggleLayer(string
layerName, bool
visible)
{
if (string.IsNullOrEmpty(layerName))
{
    Debug.LogWarning("Cannot toggle layer: Layer name is empty");
return;
}

UpdateMapView($"toggleLayer|{layerName}|{visible}");
LogDebug($"Layer '{layerName}' visibility set to {visible}");
}

// / < summary >
// / Saves
the
current
map
state
to
the
specified
file
// / < / summary >
// / < param
name = "savePath" > Path
where
the
map
should
be
saved(uses
default
path if empty) < / param >
// / < returns > True if the
save
was
successful < / returns >
               public
bool
SaveMap(string
savePath = "")
{
    string
filePath = string.IsNullOrEmpty(savePath) ? mapFilePath: savePath;

try
    {
        string
    mapData = GetMapData();
    if (string.IsNullOrEmpty(mapData))
    {
    Debug.LogError("Failed to get map data for saving");
return false;
}

File.WriteAllText(filePath, mapData);
LogDebug($"Map saved to {filePath}");
return true;
}
catch(Exception
ex)
{
Debug.LogError($"Error saving map: {ex.Message}");
return false;
}
}

// / < summary >
// / Zooms
to
specific
coordinates
on
the
map
// / < / summary >
// / < param
name = "x" > X
coordinate < / param >
// / < param
name = "y" > Y
coordinate < / param >
// / < param
name = "zoomLevel" > Zoom
level(higher
values = more
zoomed in) < / param >
               public
void
ZoomToCoordinates(float
x, float
y, float
zoomLevel)
{
    UpdateMapView($"zoomTo|{x}|{y}|{zoomLevel}");
LogDebug($"Zooming to ({x}, {y}) at zoom level {zoomLevel}");
}

// / < summary >
// / Resets
the
map
view
to
the
default
position and zoom
// / < / summary >
         public
void
ResetView()
{
    UpdateMapView("resetView");
LogDebug("Map view reset");
}

// / < summary >
// / Gets
information
about
the
current
map
// / < / summary >
// / < returns > JSON
string
with map information < / returns >
public string GetMapInformation()
{
return GetMapInfo();
}

# endregion

# region Private Methods

private
IEnumerator
LoadMapRoutine()
{
if (string.IsNullOrEmpty(mapFilePath))
    {
        Debug.LogError("Map file path is not set");
    yield
break;
}

if (!File.Exists(mapFilePath))
{
Debug.LogError($"Map file not found at path: {mapFilePath}");
yield
break;
}

try
    {
        string
    mapData = File.ReadAllText(mapFilePath);

    if (string.IsNullOrEmpty(mapData))
    {
    Debug.LogError("Map file is empty");
    yield
break;
}

// Initialize
the
Azgaar
viewer
with the map data
string azgaarUrl = string.IsNullOrEmpty(customAzgaarUrl)
? "https://azgaar.github.io/Fantasy-Map-Generator/"
: customAzgaarUrl;

InitializeAzgaarMapViewer(
mapData,
enableMapEditing,
disableGeneration,
updateFrequency,
azgaarUrl
);

LogDebug("Azgaar map viewer initialized successfully");
}
catch(Exception
ex)
{
    Debug.LogError($"Error loading map file: {ex.Message}");
}
}

private
void
LogDebug(string
message)
{
if (enableDebugLogging)
{
    Debug.Log($"[AzgaarMap] {message}");
}
}

# endregion
}

// / < summary >
// / Manages
the
texture
used
to
display
the
map
// / < / summary > \
         public


class MapTextureManager
    {
        public
    Texture2D
    Texture
    {get;
    private
    set;}

    public
    MapTextureManager(int
    width, int
    height)
    {
    // Create
    texture
    with correct format for WebGL
    Texture = new Texture2D(width, height, TextureFormat.RGBA32, false);

    // Initialize with white background
    Color[] pixels = new Color[width * height];
    for (int i = 0; i < pixels.Length; i++)
    {
    pixels[i] = Color.white;
    }

    Texture.SetPixels(pixels);
    Texture.Apply();
    }

    // / < summary >
    // / Updates the texture with data from the WebGL context
    // / This method is called from JavaScript via SendMessage
    // / < / summary >
    // / < param name="data" > Raw texture data as byte array < / param >
    public void UpdateTextureFromJS(byte[] data)
    {
    if (data == null | | data.Length == 0)
    {
    Debug.LogWarning("Received empty texture data from JavaScript");


return;
}

try
    {
        Texture.LoadRawTextureData(data);
    Texture.Apply();
    }
    catch(Exception
    ex)
    {
        Debug.LogError($"Error updating texture: {ex.Message}");
    }
    }
    }